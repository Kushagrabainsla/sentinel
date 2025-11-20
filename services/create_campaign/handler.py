import json
import os
from datetime import datetime, timezone
import boto3
from common_db import create_campaign, CampaignType, CampaignState, CampaignDeliveryType

def _get_segments_table():
    """Get DynamoDB segments table"""
    table_name = os.environ.get('DYNAMODB_SEGMENTS_TABLE')
    if not table_name:
        raise RuntimeError('DYNAMODB_SEGMENTS_TABLE environment variable not set')
    dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    return dynamodb.Table(table_name)

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

def _get_segments_table():
    """Get DynamoDB segments table"""
    import boto3
    table_name = os.environ.get('DYNAMODB_SEGMENTS_TABLE')
    if not table_name:
        raise RuntimeError('DYNAMODB_SEGMENTS_TABLE environment variable not set')
    dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    return dynamodb.Table(table_name)

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
    emails = data.get("emails")  # List of emails for segment campaigns
    segment_id = data.get("segment_id")  # Optional: existing segment ID
    campaign_type = data.get("type")
    delivery_type = data.get("delivery_type")  # "IND" for individual, "SEG" for segment
    recipient_email = data.get("recipient_email")  # For individual campaigns
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
    
    # Validate delivery type and corresponding fields
    if not delivery_type:
        delivery_type = CampaignDeliveryType.SEGMENT  # Default to segment-based
    
    if delivery_type == CampaignDeliveryType.INDIVIDUAL:
        if not recipient_email:
            return _response(400, {"error": "recipient_email is required for individual campaigns"})
        if emails or segment_id:
            return _response(400, {"error": "emails or segment_id should not be provided for individual campaigns"})
    elif delivery_type == CampaignDeliveryType.SEGMENT:
        if recipient_email:
            return _response(400, {"error": "recipient_email should not be provided for segment campaigns"})
        if not emails and not segment_id:
            return _response(400, {"error": "Either emails list or segment_id is required for segment campaigns"})
        if emails and segment_id:
            return _response(400, {"error": "Provide either emails list or segment_id, not both"})
        
        # Validate emails if provided
        if emails:
            if not isinstance(emails, list) or len(emails) == 0:
                return _response(400, {"error": "emails must be a non-empty list"})
            
            import re
            email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            invalid_emails = [email for email in emails if not email_pattern.match(email)]
            if invalid_emails:
                return _response(400, {"error": f"Invalid email addresses: {', '.join(invalid_emails[:5])}"})
    else:
        return _response(400, {"error": f"delivery_type must be '{CampaignDeliveryType.INDIVIDUAL}' for individual or '{CampaignDeliveryType.SEGMENT}' for segment campaigns"})

    try:
        # If emails provided, create a temporary segment
        final_segment_id = segment_id
        if emails and delivery_type == CampaignDeliveryType.SEGMENT:
            # Create a temporary segment for this campaign
            import uuid
            final_segment_id = str(uuid.uuid4())
            
            # Store temporary segment
            segments_table = _get_segments_table()
            import time
            segments_table.put_item(
                Item={
                    'id': final_segment_id,
                    'name': f"Campaign {name} - Recipients",
                    'description': f"Auto-generated segment for campaign: {name}",
                    'emails': list(set(email.lower().strip() for email in emails)),
                    'contact_count': len(set(emails)),
                    'created_at': int(time.time()),
                    'updated_at': int(time.time()),
                    'created_by': 'campaign_api',
                    'status': 'active',
                    'temporary': True
                }
            )
            print(f"✅ Created temporary segment {final_segment_id} with {len(set(emails))} emails")
        
        campaign_id = create_campaign(
            name=name, 
            segment_id=final_segment_id,
            campaign_type=campaign_type,
            delivery_type=delivery_type,
            recipient_email=recipient_email,
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
            "delivery_type": delivery_type,
            "recipient_email": recipient_email if delivery_type == CampaignDeliveryType.INDIVIDUAL else None,
            "segment_id": final_segment_id if delivery_type == CampaignDeliveryType.SEGMENT else None,
            "schedule_at": schedule_at,
            "execution_path": "immediate",
            "triggered": immediate_triggered
        }
        
        # Add segment info for segment campaigns
        if delivery_type == CampaignDeliveryType.SEGMENT:
            if emails:
                response_data["recipient_count"] = len(set(emails))
                response_data["temporary_segment"] = True
            else:
                response_data["temporary_segment"] = False
    elif campaign_type == CampaignType.SCHEDULED:  # Scheduled campaigns
        print(f"📅 Scheduled execution path for campaign {campaign_id}")
        scheduler_created = _create_scheduler_rule(campaign_id, schedule_at)
        
        response_data = {
            "campaign_id": campaign_id,
            "state": CampaignState.SCHEDULED,
            "type": campaign_type,
            "delivery_type": delivery_type,
            "recipient_email": recipient_email if delivery_type == CampaignDeliveryType.INDIVIDUAL else None,
            "segment_id": final_segment_id if delivery_type == CampaignDeliveryType.SEGMENT else None,
            "schedule_at": schedule_at,
            "execution_path": "scheduled",
            "auto_scheduler": scheduler_created
        }
        
        # Add segment info for segment campaigns
        if delivery_type == CampaignDeliveryType.SEGMENT:
            if emails:
                response_data["recipient_count"] = len(set(emails))
                response_data["temporary_segment"] = True
            else:
                response_data["temporary_segment"] = False
    else:
        return _response(400, {"error": "Invalid campaign type"})
    
    return _response(201, response_data)
