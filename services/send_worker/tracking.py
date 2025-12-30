import os
import time
import uuid
import json
import hashlib
import boto3
import base64
from botocore.exceptions import ClientError

_dynamo = None

def _get_dynamo():
    global _dynamo
    if _dynamo is None:
        session = boto3.session.Session()
        region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
        _dynamo = session.resource("dynamodb", region_name=region)
    return _dynamo

def update_email_tracking_status(campaign_id, email, status):
    """Update email tracking status in events table"""
    table_name = os.environ.get("DYNAMODB_EVENTS_TABLE")
    if not table_name:
        print("Warning: DYNAMODB_EVENTS_TABLE env var not set")
        return
    
    table = _get_dynamo().Table(table_name)
    
    try:
        # Record tracking status event
        event_record = {
            'id': str(uuid.uuid4()),
            'campaign_id': str(campaign_id),
            'recipient_id': hashlib.md5(email.encode()).hexdigest()[:8],
            'email': email,
            'type': 'tracking_status',
            'created_at': int(time.time()),
            'raw': json.dumps({'status': status})
        }
        
        table.put_item(Item=event_record)
    except Exception as e:
        print(f"❌ Failed to update tracking status: {e}")

def store_link_mapping(campaign_id, recipient_id, link_id, original_url, tracking_id, email, variation_id=None):
    """Store link mapping for click tracking"""
    table_name = os.environ.get("DYNAMODB_LINK_MAPPINGS_TABLE")
    if not table_name:
        print("Warning: DYNAMODB_LINK_MAPPINGS_TABLE env var not set")
        return False
    
    try:
        table = _get_dynamo().Table(table_name)
        
        # TTL: 90 days from now
        expires_at = int(time.time()) + (90 * 24 * 60 * 60)
        
        item = {
            'tracking_id': tracking_id,
            'campaign_id': str(campaign_id),
            'recipient_id': str(recipient_id),
            'email': email,
            'variation_id': variation_id,
            'link_id': link_id,
            'original_url': original_url,
            'created_at': int(time.time()),
            'expires_at': expires_at
        }
        
        table.put_item(Item=item)
        return True
        
    except Exception as e:
        print(f"❌ Failed to store link mapping: {e}")
        return False

def create_cta_tracking_link(campaign_id, recipient_id, cta_id, original_url, email, base_url=None, variation_id=None):
    """
    Create a tracking link for a specific CTA
    
    Args:
        campaign_id: Campaign identifier
        recipient_id: Recipient identifier  
        cta_id: Unique identifier for this CTA (e.g., "primary_cta", "secondary_cta")
        original_url: The actual destination URL
        email: Recipient email
        base_url: Base tracking domain
    
    Returns:
        str: Tracking redirect URL
    """
    if not base_url:
        base_url = os.environ.get("TRACKING_BASE_URL", "https://api.thesentinel.site")
    
    # Generate unique tracking ID
    tracking_id = str(uuid.uuid4())
    
    # Create tracking URL
    tracking_url = f"{base_url}/track/click/{tracking_id}"
    
    # Store mapping in database
    store_link_mapping(
        campaign_id=campaign_id,
        recipient_id=recipient_id,
        link_id=cta_id,
        original_url=original_url,
        tracking_id=tracking_id,
        email=email,
        variation_id=variation_id
    )
    
    print(f"📊 Created tracking link for CTA '{cta_id}': {original_url} -> {tracking_url}")
    
    return tracking_url

def generate_tracking_data(campaign_id, recipient_id, email, cta_links=None, base_url=None, variation_id=None):
    """Generate simple email tracking: open pixel + CTA link tracking"""
    if not base_url:
        base_url = os.environ.get("TRACKING_BASE_URL", "https://api.thesentinel.site")
    
    # Open tracking pixel - using .gif for better email client compatibility
    pixel_url = f"{base_url}/track/open/{campaign_id}/{recipient_id}.gif?email={base64.urlsafe_b64encode(email.encode()).decode()}"
    if variation_id:
        pixel_url += f"&variation_id={variation_id}"
    tracking_pixel = f'<img src="{pixel_url}" width="1" height="1" style="display:none;" alt="">'
    
    # CTA link tracking
    tracked_cta_links = {}
    if cta_links:
        for cta_id, original_url in cta_links.items():
            if original_url and original_url.startswith(('http://', 'https://')):
                tracking_url = create_cta_tracking_link(
                    campaign_id, recipient_id, cta_id, original_url, email, base_url, variation_id
                )
                tracked_cta_links[cta_id] = tracking_url
    
    # Unsubscribe link - using a unique ID and storing mapping to find email later
    unsubscribe_id = str(uuid.uuid4())
    unsubscribe_url = f"{base_url}/unsubscribe/{unsubscribe_id}"
    
    store_link_mapping(
        campaign_id=campaign_id,
        recipient_id=recipient_id,
        link_id="unsubscribe",
        original_url="UNSUBSCRIBE",
        tracking_id=unsubscribe_id,
        email=email,
        variation_id=variation_id
    )
    
    return {
        "tracked_cta_links": tracked_cta_links,
        "unsubscribe_url": unsubscribe_url,
        "tracking_pixel": tracking_pixel,
        "pixel_url": pixel_url
    }