import json
import os
from datetime import datetime, timezone
import boto3
from common_db import create_campaign

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
        # Parse schedule_at datetime
        schedule_dt = datetime.fromisoformat(schedule_at.replace('Z', '+00:00'))
        
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
    template_id = data.get("template_id")
    segment_id = data.get("segment_id")
    schedule_at = data.get("schedule_at")  # ISO8601 or None

    if not name or not template_id or not segment_id:
        return _response(400, {"error": "name, template_id, segment_id are required"})

    # Default schedule: now (UTC) if not provided
    if not schedule_at:
        schedule_at = datetime.now(timezone.utc).isoformat()

    campaign_id = create_campaign(name, template_id, segment_id, schedule_at)

    # Parse schedule time to determine execution path
    schedule_dt = datetime.fromisoformat(schedule_at.replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    time_diff = (schedule_dt - now).total_seconds()

    # Dual-path approach:
    if time_diff <= 60:  # If scheduled within 1 minute, trigger immediately
        print(f"⚡ Immediate execution path for campaign {campaign_id}")
        immediate_triggered = _trigger_immediate_campaign(campaign_id)
        
        response_data = {
            "campaign_id": campaign_id,
            "state": "sending",  # Immediate campaigns go to sending state
            "schedule_at": schedule_at,
            "execution_path": "immediate",
            "triggered": immediate_triggered
        }
    else:
        print(f"📅 Scheduled execution path for campaign {campaign_id}")
        scheduler_created = _create_scheduler_rule(campaign_id, schedule_at)
        
        response_data = {
            "campaign_id": campaign_id,
            "state": "scheduled",  # Future campaigns stay scheduled
            "schedule_at": schedule_at,
            "execution_path": "scheduled",
            "auto_scheduler": scheduler_created
        }
    
    return _response(201, response_data)
