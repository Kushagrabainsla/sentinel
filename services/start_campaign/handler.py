import json
import os
import math
import time
import hashlib
import boto3
from botocore.exceptions import ClientError

# Campaign State Enums
class CampaignState:
    SCHEDULED = "SC"  # Scheduled for future execution
    PENDING = "P"     # Pending immediate execution
    SENDING = "SE"    # Currently sending
    DONE = "D"        # Completed
    FAILED = "F"      # Failed

# Campaign Status Enums
class CampaignStatus:
    ACTIVE = "A"      # Active campaign
    INACTIVE = "I"    # Inactive campaign

# Campaign Delivery Mechanism Enums
class CampaignDeliveryType:
    INDIVIDUAL = "IND"   # Single recipient
    SEGMENT = "SEG"      # Segment-based (multiple recipients)

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
            if active_only and segment.get('status') != 'active':
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

def update_campaign_state(campaign_id, state):
    table_name = os.environ.get("DYNAMODB_CAMPAIGNS_TABLE")
    if not table_name:
        raise RuntimeError("DYNAMODB_CAMPAIGNS_TABLE env var not set")
    table = _get_dynamo().Table(table_name)
    table.update_item(
        Key={'id': str(campaign_id)},
        UpdateExpression='SET #s = :s, updated_at = :updated_at',
        ExpressionAttributeNames={'#s': 'state'},
        ExpressionAttributeValues={
            ':s': state,
            ':updated_at': int(time.time())
        }
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
    delivery_type = campaign.get('delivery_type', CampaignDeliveryType.SEGMENT)
    
    if delivery_type == CampaignDeliveryType.INDIVIDUAL:
        recipient_email = campaign.get('recipient_email')
        if not recipient_email:
            raise ValueError("No recipient_email found for individual campaign")
        return create_individual_recipient(recipient_email)
    elif delivery_type == CampaignDeliveryType.SEGMENT:
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
        update_campaign_state(campaign_id, CampaignState.FAILED)
        return {"statusCode": 400, "body": json.dumps({"error": str(e)})}
    
    if not contacts:
        update_campaign_state(campaign_id, CampaignState.DONE)
        delivery_type = campaign.get('delivery_type', CampaignDeliveryType.SEGMENT)
        message = f"no recipients found for {'individual' if delivery_type == CampaignDeliveryType.INDIVIDUAL else 'segment'} campaign"
        return {"statusCode": 200, "body": json.dumps({"message": message})}

    # Record campaign execution in segments table for tracking
    delivery_type = campaign.get('delivery_type', CampaignDeliveryType.SEGMENT)
    if delivery_type == CampaignDeliveryType.SEGMENT:
        segment_id = campaign.get('segment_id')
        recipient_emails = [c.get('email') for c in contacts if c.get('email')]
        record_segment_campaign(campaign_id, segment_id, recipient_emails)
    
    # Fan out to SQS in batches of up to 10 messages
    for batch in _chunks(contacts, 10):
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
    update_campaign_state(campaign_id, CampaignState.SENDING)

    delivery_type = campaign.get('delivery_type', CampaignDeliveryType.SEGMENT)
    response_data = {
        "campaign_id": campaign_id, 
        "enqueued": len(contacts),
        "delivery_type": delivery_type,
        "recipient_count": len(contacts)
    }
    
    if delivery_type == CampaignDeliveryType.INDIVIDUAL:
        response_data["recipient_email"] = campaign.get('recipient_email')
    else:
        response_data["segment_id"] = campaign.get('segment_id')
    
    return {"statusCode": 200, "body": json.dumps(response_data)}
