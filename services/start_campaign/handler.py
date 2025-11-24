import json
import os
import time
import hashlib
import boto3
from botocore.exceptions import ClientError

# Import common utilities and enums
# Import common utilities and enums
from common import CampaignState, CampaignStatus, CampaignDeliveryType, SegmentStatus, CampaignType
import random
from datetime import datetime, timezone

# Database utilities (moved from common_db.py)
_dynamo = None

def _get_dynamo():
    global _dynamo
    if _dynamo is None:
        session = boto3.session.Session()
        region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
        _dynamo = session.resource("dynamodb", region_name=region)
    return _dynamo

def fetch_all_emails_from_segments(active_only=True):
    """Get unique emails from all segments"""
    segments_table_name = os.environ.get("DYNAMODB_SEGMENTS_TABLE")
    if not segments_table_name:
        raise RuntimeError("DYNAMODB_SEGMENTS_TABLE env var not set")
    segments_table = _get_dynamo().Table(segments_table_name)
    
    try:
        # Scan all segments
        response = segments_table.scan()
        segments = response.get('Items', [])
        
        all_emails = set()
        for segment in segments:
            if active_only and segment.get('status') != SegmentStatus.ACTIVE.value:
                continue
                
            emails = segment.get('emails', [])
            all_emails.update(emails)
        
        # Convert to expected format
        contacts = []
        for email in all_emails:
            email_id = hashlib.md5(email.encode()).hexdigest()[:12]
            contacts.append({'id': email_id, 'email': email})
        
        print(f"Collected {len(contacts)} unique emails from {len(segments)} segments")
        return contacts
        
    except Exception as e:
        print(f"Error collecting emails from segments: {e}")
        return []

def fetch_all_active_contacts():
    """Return list of active contacts from all segments (contacts table removed)"""
    return fetch_all_emails_from_segments(active_only=True)

def fetch_segment_contacts(segment_id):
    """Return list of contacts for a specific segment as dicts: {id, email}"""
    # Validate segment_id
    if not segment_id:
        raise ValueError("segment_id cannot be empty")
    
    # Handle built-in segments - collect from all segments
    if segment_id == "all_active":
        return fetch_all_emails_from_segments(active_only=True)
    elif segment_id == "all_contacts":
        return fetch_all_emails_from_segments(active_only=False)
    
    # For custom segments, get emails from segments table
    segments_table_name = os.environ.get("DYNAMODB_SEGMENTS_TABLE")
    if not segments_table_name:
        raise RuntimeError("DYNAMODB_SEGMENTS_TABLE env var not set")
    segments_table = _get_dynamo().Table(segments_table_name)
    
    try:
        resp = segments_table.get_item(Key={'id': segment_id})
        if 'Item' not in resp:
            print(f"Warning: Segment '{segment_id}' not found")
            return []
        
        segment = resp['Item']
        emails = segment.get('emails', [])
        
        # Convert emails to contact format with generated IDs
        contacts = []
        for i, email in enumerate(emails):
            # Generate consistent ID based on email
            email_id = hashlib.md5(f"{segment_id}:{email}".encode()).hexdigest()[:12]
            contacts.append({'id': email_id, 'email': email})
        
        print(f"Found {len(contacts)} contacts for segment '{segment_id}'")
        return contacts
        
    except Exception as e:
        print(f"Error fetching segment '{segment_id}': {e}")
        return []

def create_individual_recipient(recipient_email):
    """Create a single recipient record for individual campaigns"""
    # For individual campaigns, create a synthetic recipient ID
    recipient_id = hashlib.md5(recipient_email.encode()).hexdigest()[:8]
    return [{'id': recipient_id, 'email': recipient_email}]

def record_segment_campaign(campaign_id, segment_id, recipient_emails):
    """Record campaign execution by updating segment with execution metadata"""
    segments_table_name = os.environ.get("DYNAMODB_SEGMENTS_TABLE")
    if not segments_table_name:
        raise RuntimeError("DYNAMODB_SEGMENTS_TABLE env var not set")
    segments_table = _get_dynamo().Table(segments_table_name)
    
    # For built-in segments, don't record in segments table
    if segment_id in ['all_active', 'all_contacts']:
        print(f"✅ Campaign {campaign_id} sent to built-in segment '{segment_id}' with {len(recipient_emails)} recipients")
        return
    
    try:
        # Update segment with last execution info
        segments_table.update_item(
            Key={'id': segment_id},
            UpdateExpression='SET last_campaign_id = :cid, last_execution_at = :time, last_recipient_count = :count',
            ExpressionAttributeValues={
                ':cid': str(campaign_id),
                ':time': int(time.time()),
                ':count': len(recipient_emails)
            }
        )
        print(f"✅ Recorded segment campaign execution for segment '{segment_id}', campaign {campaign_id}")
    except Exception as e:
        print(f"❌ Failed to record segment campaign: {e}")

def update_campaign_state(campaign_id, state, recipient_count=None, sent_count=None):
    table_name = os.environ.get("DYNAMODB_CAMPAIGNS_TABLE")
    if not table_name:
        raise RuntimeError("DYNAMODB_CAMPAIGNS_TABLE env var not set")
    table = _get_dynamo().Table(table_name)
    
    update_expr = 'SET #s = :s, updated_at = :updated_at'
    expr_values = {
        ':s': state,
        ':updated_at': int(time.time())
    }
    
    if recipient_count is not None:
        update_expr += ', recipient_count = :rc'
        expr_values[':rc'] = recipient_count
        
    if sent_count is not None:
        update_expr += ', sent_count = :sc'
        expr_values[':sc'] = sent_count

    table.update_item(
        Key={'id': str(campaign_id)},
        UpdateExpression=update_expr,
        ExpressionAttributeNames={'#s': 'state'},
        ExpressionAttributeValues=expr_values
    )

def fetch_campaign_details(campaign_id):
    """Fetch campaign details including direct email content"""
    table_name = os.environ.get("DYNAMODB_CAMPAIGNS_TABLE")
    if not table_name:
        raise RuntimeError("DYNAMODB_CAMPAIGNS_TABLE env var not set")
    table = _get_dynamo().Table(table_name)
    
    try:
        response = table.get_item(Key={'id': str(campaign_id)})
        return response.get('Item')
    except ClientError as e:
        print(f"Error fetching campaign {campaign_id}: {e}")
        return None

def get_campaign_recipients(campaign):
    """Get recipients based on campaign delivery type"""
    delivery_type = campaign.get('delivery_type', CampaignDeliveryType.SEGMENT.value)

    if delivery_type == CampaignDeliveryType.INDIVIDUAL.value:
        recipient_email = campaign.get('recipient_email')
        if not recipient_email:
            raise ValueError("No recipient_email found for individual campaign")
        return create_individual_recipient(recipient_email)
    elif delivery_type == CampaignDeliveryType.SEGMENT.value:
        segment_id = campaign.get('segment_id')
        if not segment_id:
            raise ValueError("No segment_id found for segment campaign")
        return fetch_segment_contacts(segment_id)
    else:
        raise ValueError(f"Unknown delivery_type: {delivery_type}")

SQS_URL = os.environ.get("SEND_QUEUE_URL")  # set by Terraform (queues module)

sqs = boto3.client("sqs")

def _chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def create_ab_test_scheduler(campaign_id, decision_time):
    """Create EventBridge Scheduler rule for A/B test analysis"""
    scheduler = boto3.client("scheduler")
    analyzer_lambda_arn = os.environ.get("AB_TEST_ANALYZER_LAMBDA_ARN")
    scheduler_role_arn = os.environ.get("EVENTBRIDGE_ROLE_ARN")
    
    if not analyzer_lambda_arn or not scheduler_role_arn:
        print(f"Missing scheduler config: lambda_arn={analyzer_lambda_arn}, role_arn={scheduler_role_arn}")
        return False
    
    try:
        # Convert epoch timestamp to datetime (handle Decimal from DynamoDB)
        # Force conversion to float first to handle Decimal safely, then to int
        decision_time_int = int(float(decision_time))
        schedule_dt = datetime.fromtimestamp(decision_time_int, timezone.utc)
        
        # Only create scheduler if it's in the future
        if schedule_dt <= datetime.now(timezone.utc):
            print(f"Decision time {decision_time} is in the past, skipping scheduler")
            return False
        
        # Create one-time schedule
        schedule_name = f"analyze-ab-test-{campaign_id}"
        
        scheduler.create_schedule(
            Name=schedule_name,
            Description=f"Analyze A/B test for campaign {campaign_id}",
            ScheduleExpression=f"at({schedule_dt.strftime('%Y-%m-%dT%H:%M:%S')})",
            Target={
                "Arn": analyzer_lambda_arn,
                "RoleArn": scheduler_role_arn,
                "Input": json.dumps({"campaign_id": campaign_id})
            },
            FlexibleTimeWindow={"Mode": "OFF"},
            ActionAfterCompletion="DELETE"
        )
        
        print(f"✅ Created A/B test analyzer scheduler: {schedule_name} for {decision_time}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create analyzer scheduler: {e}")
        return False

def lambda_handler(event, _context):
    """
    Event can be:
      - direct invoke: {"campaign_id": 123}
      - API Gateway payload: {"body": "{\"campaign_id\":123}"}
      - EventBridge Scheduler input: {"campaign_id":123}
    """
    payload = event
    if "body" in event and isinstance(event["body"], str):
        try:
            payload = json.loads(event["body"])
        except Exception:
            payload = {}

    campaign_id = payload.get("campaign_id")
    if not campaign_id:
        return {"statusCode": 400, "body": json.dumps({"error": "campaign_id required"})}

    # Fetch campaign details including direct email content
    campaign = fetch_campaign_details(campaign_id)
    if not campaign:
        return {"statusCode": 404, "body": json.dumps({"error": "Campaign not found"})}

    # Materialize recipients based on campaign delivery type
    try:
        contacts = get_campaign_recipients(campaign)
    except ValueError as e:
        update_campaign_state(campaign_id, CampaignState.FAILED.value)
        return {"statusCode": 400, "body": json.dumps({"error": str(e)})}
    
    if not contacts:
        update_campaign_state(campaign_id, CampaignState.DONE.value)
        delivery_type = campaign.get('delivery_type', CampaignDeliveryType.SEGMENT.value)
        message = f"no recipients found for {'individual' if delivery_type == CampaignDeliveryType.INDIVIDUAL.value else 'segment'} campaign"
        return {"statusCode": 200, "body": json.dumps({"message": message})}

    # Record campaign execution in segments table for tracking
    delivery_type = campaign.get('delivery_type', CampaignDeliveryType.SEGMENT.value)
    if delivery_type == CampaignDeliveryType.SEGMENT.value:
        segment_id = campaign.get('segment_id')
        recipient_emails = [c.get('email') for c in contacts if c.get('email')]
        record_segment_campaign(campaign_id, segment_id, recipient_emails)
    
    # Check for A/B Test
    campaign_type = campaign.get('type')
    
    if campaign_type == CampaignType.AB_TEST.value:
        print(f"🧪 Processing A/B Test for campaign {campaign_id}")
        ab_config = campaign.get('ab_test_config', {})
        variations = campaign.get('variations', [])
        
        if not ab_config or len(variations) != 3:
            print("❌ Invalid A/B test config or variations")
            update_campaign_state(campaign_id, CampaignState.FAILED.value)
            return {"statusCode": 400, "body": json.dumps({"error": "Invalid A/B test config"})}
            
        test_percentage = float(ab_config.get('test_percentage', 10))
        decision_time = ab_config.get('decision_time') # Epoch timestamp
        
        # Shuffle contacts
        random.shuffle(contacts)
        
        total_contacts = len(contacts)
        # Calculate test group size (per variation)
        # If test_percentage is 30%, then 30% of TOTAL users are tested.
        # So each variation gets 10%.
        test_group_size = int(total_contacts * (test_percentage / 100) / 3)
        
        # Ensure at least 1 user per group if possible
        if test_group_size < 1 and total_contacts >= 3:
            test_group_size = 1
            
        print(f"📊 A/B Split: Total={total_contacts}, Test%={test_percentage}, GroupSize={test_group_size}")
        
        group_a = contacts[:test_group_size]
        group_b = contacts[test_group_size:test_group_size*2]
        group_c = contacts[test_group_size*2:test_group_size*3]
        remainder = contacts[test_group_size*3:]
        
        groups = [
            (group_a, variations[0], "A"),
            (group_b, variations[1], "B"),
            (group_c, variations[2], "C")
        ]
        
        enqueued_count = 0
        
        for group_contacts, variation, var_id in groups:
            print(f"📤 Sending Variation {var_id} to {len(group_contacts)} recipients")
            
            for batch in _chunks(group_contacts, 10):
                entries = []
                for c in batch:
                    message_body = {
                        "campaign_id": campaign_id,
                        "recipient_id": c["id"],
                        "email": c["email"],
                        "variation_id": var_id, # Pass variation ID
                        "template_data": {
                            "subject": variation.get("subject"),
                            "html_body": variation.get("content"), # Assuming 'content' key from generate_email
                            "from_email": campaign.get("from_email", "noreply@thesentinel.site"),
                            "from_name": campaign.get("from_name", "Sentinel")
                        }
                    }
                    
                    entries.append({
                        "Id": str(c["id"]),
                        "MessageBody": json.dumps(message_body),
                    })
                
                if entries:
                    sqs.send_message_batch(QueueUrl=SQS_URL, Entries=entries)
                    enqueued_count += len(entries)

        # Schedule the analyzer
        if decision_time:
            create_ab_test_scheduler(campaign_id, decision_time)
            
        # Mark as SENDING (or PARTIAL?)
        # We'll keep it as SENDING until the analyzer runs and finishes the job
        update_campaign_state(campaign_id, CampaignState.SENDING.value, recipient_count=enqueued_count, sent_count=enqueued_count)
        
        return {"statusCode": 200, "body": json.dumps({
            "campaign_id": campaign_id,
            "enqueued": enqueued_count,
            "message": f"Started A/B test with {enqueued_count} recipients. Remainder: {len(remainder)}"
        })}

    # Standard Campaign Logic
    # Fan out to SQS in batches of up to 10 messages
    for batch in _chunks(contacts, 10):
        # ... (sqs sending logic)
        entries = []
        for c in batch:
            message_body = {
                "campaign_id": campaign_id,
                "recipient_id": c["id"],
                "email": c["email"],
                "template_data": {
                    "subject": campaign.get("email_subject", campaign.get("subject", "")),
                    "html_body": campaign.get("email_body", campaign.get("html_body", "")),
                    "from_email": campaign.get("from_email", "noreply@thesentinel.site"),
                    "from_name": campaign.get("from_name", "Sentinel")
                }
            }
            
            # Inline tracking is used by default
            
            entries.append({
                "Id": str(c["id"]),
                "MessageBody": json.dumps(message_body),
            })
        sqs.send_message_batch(QueueUrl=SQS_URL, Entries=entries)

    # Mark campaign as "sending"
    update_campaign_state(campaign_id, CampaignState.SENDING.value, recipient_count=len(contacts), sent_count=len(contacts))

    delivery_type = campaign.get('delivery_type', CampaignDeliveryType.SEGMENT.value)
    response_data = {
        "campaign_id": campaign_id, 
        "enqueued": len(contacts),
        "delivery_type": delivery_type,
        "recipient_count": len(contacts)
    }
    
    if delivery_type == CampaignDeliveryType.INDIVIDUAL.value:
        response_data["recipient_email"] = campaign.get('recipient_email')
    else:
        response_data["segment_id"] = campaign.get('segment_id')
    
    return {"statusCode": 200, "body": json.dumps(response_data)}
