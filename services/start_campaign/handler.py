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

# ... (fetch_campaign_details, get_campaign_recipients, etc.)

# ... (inside lambda_handler)

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
