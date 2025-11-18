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

def generate_inline_tracking_pixel(campaign_id, recipient_id):
    """
    Generate an inline data URI tracking pixel to avoid external image warnings.
    Creates a 1x1 transparent PNG encoded as base64 data URI.
    """
    # 1x1 transparent PNG as base64
    transparent_png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    # Create data URI
    pixel_data_uri = f"data:image/png;base64,{transparent_png_b64}"
    
    return {
        "pixel_html": f'<img src="{pixel_data_uri}" width="1" height="1" style="display:none;" alt="" data-campaign="{campaign_id}" data-recipient="{recipient_id}">',
        "pixel_data_uri": pixel_data_uri
    }

def generate_smart_tracking_pixel(campaign_id, recipient_id, email, base_url=None):
    """
    Generate a smart hybrid tracking pixel that combines inline and external methods.
    This provides the best balance between tracking accuracy and avoiding security warnings.
    """
    if not base_url:
        base_url = os.environ.get("TRACKING_BASE_URL", "https://api.thesentinel.site")
    
    # Get inline pixel
    inline_pixel = generate_inline_tracking_pixel(campaign_id, recipient_id)
    
    # External tracking URL for server-side analytics
    external_tracking_url = f"{base_url}/track/open/{campaign_id}/{recipient_id}.png?email={email}"
    
    # Create smart hybrid tracking HTML - inline pixel visible, external hidden
    smart_tracking_html = f"""
{inline_pixel["pixel_html"]}
<div style="display:none;width:0;height:0;overflow:hidden;opacity:0;">
    <img src="{external_tracking_url}" width="1" height="1" alt="" style="display:none;">
</div>"""
    
    return {
        "tracking_pixel_html": smart_tracking_html,
        "tracking_pixel_url": external_tracking_url,
        "inline_pixel_url": inline_pixel["pixel_data_uri"],
        "tracking_method": "Smart Hybrid (Inline + Hidden External)"
    }

def generate_tracking_data(campaign_id, recipient_id, email, cta_links=None, base_url=None, tracking_mode="smart"):
    """
    Generate tracking URLs and data for email with enhanced pixel strategies.
    
    Args:
        campaign_id: Campaign identifier
        recipient_id: Recipient identifier
        email: Recipient email address
        cta_links: Dict of CTA links to track {"cta_id": "original_url"}
        base_url: Base tracking domain
        tracking_mode: "smart", "inline", "external", "disabled"
    
    Returns:
        Enhanced tracking data with improved pixel methods
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
    
    # Generate tracking pixel based on mode
    tracking_data = {
        "unsubscribe_url": unsubscribe_url,
        "tracked_cta_links": tracked_cta_links,
        "tracking_mode": tracking_mode
    }
    
    if tracking_mode == "disabled":
        print("🚫 Tracking disabled")
        tracking_data.update({
            "tracking_pixel_html": "",
            "tracking_pixel_url": "",
            "tracking_method": "Disabled"
        })
    elif tracking_mode == "inline":
        # Use only inline data URI pixel (no external requests)
        inline_pixel = generate_inline_tracking_pixel(campaign_id, recipient_id)
        tracking_data.update({
            "tracking_pixel_html": inline_pixel["pixel_html"],
            "tracking_pixel_url": inline_pixel["pixel_data_uri"],
            "tracking_method": "Inline Data URI (No External Requests)"
        })
        print(f"📊 Generated inline tracking pixel (no external requests)")
    elif tracking_mode == "external":
        # Traditional external image pixel
        tracking_pixel_url = f"{base_url}/track/open/{campaign_id}/{recipient_id}.png?email={email}"
        tracking_data.update({
            "tracking_pixel_html": f'<img src="{tracking_pixel_url}" width="1" height="1" style="display:none;" alt="">',
            "tracking_pixel_url": tracking_pixel_url,
            "tracking_method": "External Image Pixel"
        })
        print(f"📊 Generated external tracking pixel")
    else:  # tracking_mode == "smart" (default)
        # Smart hybrid tracking for best balance
        smart_tracking = generate_smart_tracking_pixel(campaign_id, recipient_id, email, base_url)
        tracking_data.update(smart_tracking)
        print(f"📊 Generated smart hybrid tracking pixel")
    
    return tracking_data