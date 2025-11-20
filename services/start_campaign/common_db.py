import os
import time
import uuid
from datetime import datetime, timezone
import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

# Campaign Enums (matching create_campaign)
class CampaignState:
    SCHEDULED = "SC"  # Scheduled for future execution
    PENDING = "P"     # Pending immediate execution
    SENDING = "SE"    # Currently sending
    DONE = "D"        # Completed
    FAILED = "F"      # Failed

class CampaignStatus:
    ACTIVE = "A"      # Active campaign
    INACTIVE = "I"    # Inactive campaign

# Campaign Delivery Mechanism Enums
class CampaignDeliveryType:
    INDIVIDUAL = "IND"   # Single recipient
    SEGMENT = "SEG"      # Segment-based (multiple recipients)

_dynamo = None

def _get_dynamo():
    global _dynamo
    if _dynamo is None:
        session = boto3.session.Session()
        region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
        _dynamo = session.resource("dynamodb", region_name=region)
    return _dynamo

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
            import hashlib
            email_id = hashlib.md5(f"{segment_id}:{email}".encode()).hexdigest()[:12]
            contacts.append({'id': email_id, 'email': email})
        
        print(f"Found {len(contacts)} contacts for segment '{segment_id}'")
        return contacts
        
    except Exception as e:
        print(f"Error fetching segment '{segment_id}': {e}")
        return []

def fetch_all_emails_from_segments(active_only=True):
    """Fallback: Collect all emails from all segments when contacts table not available"""
    segments_table_name = os.environ.get("DYNAMODB_SEGMENTS_TABLE")
    if not segments_table_name:
        print("Warning: DYNAMODB_SEGMENTS_TABLE env var not set")
        return []
    
    segments_table = _get_dynamo().Table(segments_table_name)
    
    try:
        # Get all segments
        response = segments_table.scan()
        segments = response.get('Items', [])
        
        all_emails = set()
        for segment in segments:
            # Skip temporary segments or apply status filter
            if active_only and segment.get('status') != 'active':
                continue
                
            emails = segment.get('emails', [])
            all_emails.update(emails)
        
        # Convert to expected format
        contacts = []
        for email in all_emails:
            import hashlib
            email_id = hashlib.md5(email.encode()).hexdigest()[:12]
            contacts.append({'id': email_id, 'email': email})
        
        print(f"Collected {len(contacts)} unique emails from {len(segments)} segments")
        return contacts
        
    except Exception as e:
        print(f"Error collecting emails from segments: {e}")
        return []

def create_individual_recipient(recipient_email):
    """Create a single recipient record for individual campaigns"""
    # For individual campaigns, create a synthetic recipient ID
    import hashlib
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

# Analytics are tracked in separate tables/services
# Campaign table only contains campaign configuration
