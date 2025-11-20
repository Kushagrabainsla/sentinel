import json
import os
from datetime import datetime, timezone
import boto3
from common_db import create_campaign, CampaignType, CampaignState

def _parse_body(event):
    if isinstance(event, dict) and "body" in event:
        body = event["body"]
        if event.get("isBase64Encoded"):
            import base64
            body = base64.b64decode(body).decode("utf-8")
    else:
        body = event
    try:
        return json.loads(body or "{}")
    except Exception:
        return {}

def _response(code, body):
    return {
        "statusCode": code,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body),
    }

def _create_scheduler_rule(campaign_id, schedule_at):
    """Create EventBridge Scheduler rule to automatically start campaign"""
    scheduler = boto3.client("scheduler")
    start_lambda_arn = os.environ.get("START_CAMPAIGN_LAMBDA_ARN")
    scheduler_role_arn = os.environ.get("EVENTBRIDGE_ROLE_ARN")
    
    if not start_lambda_arn or not scheduler_role_arn:
        print(f"Missing scheduler config: lambda_arn={start_lambda_arn}, role_arn={scheduler_role_arn}")
        return False
    
    try:
        # Convert epoch timestamp to datetime
        schedule_dt = datetime.fromtimestamp(schedule_at, timezone.utc)
        
        # Only create scheduler if it's in the future
        if schedule_dt <= datetime.now(timezone.utc):
            print(f"Schedule time {schedule_at} is in the past, skipping scheduler")
            return False
        
        # Create one-time schedule
        schedule_name = f"start-campaign-{campaign_id}"
        
        scheduler.create_schedule(
            Name=schedule_name,
            Description=f"Auto-start campaign {campaign_id}",
            ScheduleExpression=f"at({schedule_dt.strftime('%Y-%m-%dT%H:%M:%S')})",
            Target={
                "Arn": start_lambda_arn,
                "RoleArn": scheduler_role_arn,
                "Input": json.dumps({"campaign_id": campaign_id})
            },
            FlexibleTimeWindow={"Mode": "OFF"},
            ActionAfterCompletion="DELETE"  # Auto-delete after execution
        )
        
        print(f"✅ Created scheduler rule: {schedule_name} for {schedule_at}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create scheduler: {e}")
        return False

def _trigger_immediate_campaign(campaign_id):
    """Directly invoke start_campaign Lambda for immediate execution"""
    lambda_client = boto3.client("lambda")
    start_lambda_arn = os.environ.get("START_CAMPAIGN_LAMBDA_ARN")
    
    if not start_lambda_arn:
        print(f"Missing start_campaign Lambda ARN")
        return False
    
    try:
        # Extract function name from ARN
        function_name = start_lambda_arn.split(":")[-1]
        
        # Invoke start_campaign Lambda directly
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='Event',  # Async invocation
            Payload=json.dumps({"campaign_id": campaign_id})
        )
        
        print(f"✅ Triggered immediate campaign start: {campaign_id}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to trigger immediate campaign: {e}")
        return False

def lambda_handler(event, _context):
    data = _parse_body(event)
    name = data.get("name")
    segment_id = data.get("segment_id")
    campaign_type = data.get("type")
    schedule_at = data.get("schedule_at")  # Epoch timestamp or None
    
    # Direct email content is required
    subject = data.get("subject")
    html_body = data.get("html_body")
    from_email = data.get("from_email")
    from_name = data.get("from_name")
    
    # Inline tracking is used by default for optimal deliverability

    # Validate required fields
    if not name:
        return _response(400, {"error": "name is required"})
    
    if not campaign_type:
        return _response(400, {"error": f"type is required ({CampaignType.IMMEDIATE} for immediate, {CampaignType.SCHEDULED} for scheduled)"})
    
    if not (subject and html_body):
        return _response(400, {"error": "subject and html_body are required"})
    
    if not segment_id:
        segment_id = "all_active"  # Default segment

    try:
        campaign_id = create_campaign(
            name=name, 
            segment_id=segment_id,
            campaign_type=campaign_type,
            schedule_at=schedule_at,
            subject=subject,
            html_body=html_body,
            from_email=from_email,
            from_name=from_name
        )
    except ValueError as e:
        return _response(400, {"error": str(e)})

    # Dual-path approach based on campaign type:
    if campaign_type == CampaignType.IMMEDIATE:  # Immediate campaigns
        print(f"⚡ Immediate execution path for campaign {campaign_id}")
        immediate_triggered = _trigger_immediate_campaign(campaign_id)
        
        response_data = {
            "campaign_id": campaign_id,
            "state": CampaignState.PENDING,
            "type": campaign_type,
            "schedule_at": schedule_at,
            "execution_path": "immediate",
            "triggered": immediate_triggered
        }
    elif campaign_type == CampaignType.SCHEDULED:  # Scheduled campaigns
        print(f"📅 Scheduled execution path for campaign {campaign_id}")
        scheduler_created = _create_scheduler_rule(campaign_id, schedule_at)
        
        response_data = {
            "campaign_id": campaign_id,
            "state": CampaignState.SCHEDULED,
            "type": campaign_type,
            "schedule_at": schedule_at,
            "execution_path": "scheduled",
            "auto_scheduler": scheduler_created
        }
    else:
        return _response(400, {"error": "Invalid campaign type"})
    
    return _response(201, response_data)
