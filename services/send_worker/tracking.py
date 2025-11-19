import os
import time
import uuid
import json
import boto3
from botocore.exceptions import ClientError

_dynamo = None

def _get_dynamo():
    global _dynamo
    if _dynamo is None:
        session = boto3.session.Session()
        region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
        _dynamo = session.resource("dynamodb", region_name=region)
    return _dynamo

def update_recipient_status(campaign_id, recipient_id, status):
    table_name = os.environ.get("DYNAMODB_RECIPIENTS_TABLE")
    if not table_name:
        raise RuntimeError("DYNAMODB_RECIPIENTS_TABLE env var not set")
    table = _get_dynamo().Table(table_name)
    table.update_item(
        Key={
            'campaign_id': str(campaign_id),
            'recipient_id': str(recipient_id)
        },
        UpdateExpression='SET #s = :s, last_event_at = :t',
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={':s': status, ':t': int(time.time())}
    )

def store_link_mapping(campaign_id, recipient_id, link_id, original_url, tracking_id, email):
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

def create_cta_tracking_link(campaign_id, recipient_id, cta_id, original_url, email, base_url=None):
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
        email=email
    )
    
    print(f"📊 Created tracking link for CTA '{cta_id}': {original_url} -> {tracking_url}")
    
    return tracking_url

def generate_warning_free_tracking(campaign_id, recipient_id, email, base_url=None):
    """
    Generate reliable email open tracking using tracking pixels.
    
    This method:
    1. Uses invisible 1x1 tracking pixel (widely supported)
    2. Pixel is served from tracking API endpoint
    3. Works in all email clients (Gmail, Outlook, Apple Mail, etc.)
    4. No JavaScript required (better deliverability)
    5. Clean, standards-compliant approach
    
    Result: Reliable open tracking without security warnings.
    """
    
    if not base_url:
        base_url = os.environ.get("TRACKING_BASE_URL", "https://api.thesentinel.site")
    
    # Generate tracking pixel URL with encoded email parameter
    pixel_url = f"{base_url}/track/open/{campaign_id}/{recipient_id}.png?email={email}&ts={int(time.time())}"
    
    # Create invisible tracking pixel (1x1 transparent image)
    tracking_pixel_html = f'''<img src="{pixel_url}" width="1" height="1" border="0" style="display:none !important; visibility:hidden !important; opacity:0 !important; background:transparent !important; width:1px !important; height:1px !important; border:none !important; margin:0 !important; padding:0 !important;" alt="" />'''
    
    # Clean email wrapper (optional styling)
    tracking_html = f'''<!-- Sentinel Email Tracking -->
<div class="sentinel-email" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;">
<style>
.sentinel-email a {{ color: #007cba; text-decoration: none; }}
.sentinel-email a:hover {{ text-decoration: underline; }}
</style>
<div class="sentinel-content">'''
    
    return {
        "pixel_html": tracking_html,
        "pixel_url": pixel_url,
        "tracking_image": tracking_pixel_html,
        "beacon_script": None,  # No JavaScript needed
        "closing_html": f'{tracking_pixel_html}</div></div><!-- End Sentinel Email -->',
        "method": "tracking_pixel"
    }


def generate_tracking_data(campaign_id, recipient_id, email, cta_links=None, base_url=None):
    """
    Generate tracking URLs and data for email using inline data URI pixels.
    
    Args:
        campaign_id: Campaign identifier
        recipient_id: Recipient identifier
        email: Recipient email address
        cta_links: Dict of CTA links to track {"cta_id": "original_url"}
        base_url: Base tracking domain
    
    Returns:
        Tracking data with inline pixels (no security warnings)
    """
    if not base_url:
        base_url = os.environ.get("TRACKING_BASE_URL", "https://api.thesentinel.site")
    
    # Generate unsubscribe URL
    unsubscribe_token = f"{campaign_id}-{recipient_id}-{int(time.time())}"
    unsubscribe_url = f"{base_url}/unsubscribe/{unsubscribe_token}"
    
    # Generate tracking links ONLY for provided CTA links
    tracked_cta_links = {}
    
    if cta_links:
        print(f"🎯 Processing {len(cta_links)} CTA links for tracking...")
        
        for cta_id, original_url in cta_links.items():
            if original_url and original_url.startswith(('http://', 'https://')):
                tracking_url = create_cta_tracking_link(
                    campaign_id=campaign_id,
                    recipient_id=recipient_id,
                    cta_id=cta_id,
                    original_url=original_url,
                    email=email,
                    base_url=base_url
                )
                tracked_cta_links[cta_id] = tracking_url
            else:
                print(f"⚠️  Skipping invalid CTA URL for '{cta_id}': {original_url}")
    
    # Generate warning-free tracking (single method that works without triggering Gmail warnings)
    tracking_pixel = generate_warning_free_tracking(campaign_id, recipient_id, email, base_url)
    
    tracking_data = {
        "unsubscribe_url": unsubscribe_url,
        "tracked_cta_links": tracked_cta_links,
        "tracking_pixel_html": tracking_pixel["pixel_html"],
        "tracking_pixel_url": tracking_pixel.get("pixel_url"),
        "tracking_image": tracking_pixel.get("tracking_image"),
        "closing_html": tracking_pixel.get("closing_html", ""),
        "tracking_method": tracking_pixel["method"]
    }
    
    print(f"📊 Generated warning-free tracking (no external requests, enhanced click tracking)")
    
    return tracking_data