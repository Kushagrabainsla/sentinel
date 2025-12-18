import json
import os
import re
import time
import uuid
import hashlib
import boto3
from botocore.exceptions import ClientError
from tracking import generate_tracking_data

# Import common utilities and enums
from common import DeliveryStatus, EventType, exponential_backoff_retry, is_retryable_error, add_dynamic_image, get_users_table, get_campaigns_table, send_gmail

# Database utilities (moved from common_db.py)
_dynamo = None

def _get_dynamo():
    global _dynamo
    if _dynamo is None:
        session = boto3.session.Session()
        region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
        _dynamo = session.resource("dynamodb", region_name=region)
    return _dynamo

def update_email_status_in_events(campaign_id, email, status):
    """Record email send status in events table instead of recipients table"""
    table_name = os.environ.get("DYNAMODB_EVENTS_TABLE")
    if not table_name:
        print("Warning: DYNAMODB_EVENTS_TABLE env var not set")
        return
    
    table = _get_dynamo().Table(table_name)
    
    try:
        # Create a send status event
        event_record = {
            'id': str(uuid.uuid4()),
            'campaign_id': str(campaign_id),
            'recipient_id': hashlib.md5(email.encode()).hexdigest()[:8],  # Generate consistent ID from email
            'email': email,
            'type': EventType.SENT.value,
            'created_at': int(time.time()),
            'raw': json.dumps({'status': status})
        }
        
        table.put_item(Item=event_record)
    except Exception as e:
        print(f"❌ Failed to record email status: {e}")

ses = boto3.client("ses")
FROM = os.environ.get("SES_FROM_ADDRESS")       # set in Terraform


def extract_cta_links(html_content):
    """
    Extract CTA links from HTML content, excluding footer/policy links.
    Returns dict of {cta_id: original_url} for links that should be tracked.
    """
    if not html_content:
        return {}
    
    # Pattern to find anchor tags with href attributes
    link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
    matches = re.findall(link_pattern, html_content, re.IGNORECASE | re.DOTALL)
    
    cta_links = {}
    excluded_patterns = [
        r'#',  # anchor links
        r'javascript:',  # javascript links
    ]
    
    def clean_text_for_display(text):
        """Clean link text for display purposes"""
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text.strip())
        return clean_text or 'Unknown Link'
    
    used_ids = set()
    
    for i, (url, link_text) in enumerate(matches):
        # Skip excluded links
        should_exclude = any(re.search(pattern, url.lower()) or re.search(pattern, link_text.lower()) 
                           for pattern in excluded_patterns)
        
        if not should_exclude and url.startswith(('http://', 'https://')):
            # Generate meaningful ID with format: "Text Value (LINK URL)"
            display_text = clean_text_for_display(link_text)
            base_id = f"{display_text} ({url})"
            
            # Handle duplicates by adding a number suffix
            cta_id = base_id
            counter = 1
            while cta_id in used_ids:
                cta_id = f"{display_text} ({url}) #{counter}"
                counter += 1
            
            used_ids.add(cta_id)
            cta_links[cta_id] = url
    
    print(f"Extracted {json.dumps(cta_links)} CTA links for tracking")
    return cta_links

def optimize_html_for_deliverability(html_content):
    """
    Optimize HTML content to reduce security warnings while maintaining functionality.
    """
    if not html_content:
        return html_content
    
    # Remove potentially problematic CSS properties that trigger security warnings
    problematic_patterns = [
        r'background:\s*linear-gradient[^;]+;?',
        r'box-shadow:[^;]+;?',
        r'text-shadow:[^;]+;?',
        r'filter:[^;]+;?',
        r'transform:[^;]+;?',
        r'animation:[^;]+;?',
        r'transition:[^;]+;?'
    ]
    
    optimized_html = html_content
    for pattern in problematic_patterns:
        optimized_html = re.sub(pattern, '', optimized_html, flags=re.IGNORECASE)
    
    # Clean up empty style attributes
    optimized_html = re.sub(r'style=""', '', optimized_html)
    optimized_html = re.sub(r'style="\s*"', '', optimized_html)
    
    return optimized_html

def lambda_handler(event, _context):
    """
    Triggered by SQS event. Each record has body:
    {"campaign_id":123, "recipient_id":456, "email":"user@example.com"}
    """
    for rec in event.get("Records", []):
        body = json.loads(rec["body"])
        campaign_id = body["campaign_id"]
        recipient_id = body["recipient_id"]
        recipient_id = body["recipient_id"]
        email = body["email"]
        variation_id = body.get("variation_id")

        try:
            # Get template data from the message
            msg_template_data = body.get("template_data", {})
            html_body = msg_template_data.get("html_body", "")
            
            print(f"📧 Processing email for {email} (Campaign: {campaign_id})")
            print(f"🎯 Using external tracking pixels for Gmail compatibility")
            
            # Extract CTA links from HTML content for tracking
            cta_links = extract_cta_links(html_body)
            if cta_links:
                print(f"🔗 Found {len(cta_links)} CTA links to track")
            
            # Generate tracking data with inline pixels (no security warnings)
            tracking_data = generate_tracking_data(
                campaign_id=campaign_id, 
                recipient_id=recipient_id, 
                email=email,
                cta_links=cta_links,
                variation_id=variation_id
            )
            
            # Replace original CTA links with tracking links in HTML
            processed_html = html_body
            if tracking_data.get("tracked_cta_links"):
                for cta_id, original_url in cta_links.items():
                    if cta_id in tracking_data["tracked_cta_links"]:
                        tracking_url = tracking_data["tracked_cta_links"][cta_id]
                        processed_html = processed_html.replace(original_url, tracking_url)
                        print(f"🔄 Replaced CTA link: {cta_id}")
            
            # Optimize HTML for better deliverability
            processed_html = optimize_html_for_deliverability(processed_html)
            
            # Add dynamic image if campaign specifies one
            dynamic_image_url = msg_template_data.get("dynamic_image_url")
            if dynamic_image_url:
                dynamic_image_position = msg_template_data.get("dynamic_image_position", "top")
                processed_html = add_dynamic_image(
                    processed_html,
                    dynamic_image_url,
                    alt_text=msg_template_data.get("dynamic_image_alt", "Dynamic Content"),
                    position=dynamic_image_position,
                    campaign_id=campaign_id,
                    recipient_id=recipient_id,
                    email=email
                )
                print(f"🖼️ Added dynamic image: {dynamic_image_url}")
            
            # Prepare template data for SES
            template_data = {
                "name": email.split("@")[0],
                "subject": msg_template_data.get("subject", "Newsletter"),
                "html_body": processed_html,
            }
            
            print(f"📧 Sending email to {email} for campaign {campaign_id}")
            if tracking_data.get("tracked_cta_links"):
                print(f"🎯 CTA links tracked: {list(tracking_data['tracked_cta_links'].keys())}")
            
            # Add tracking pixel to HTML content
            html_content = template_data["html_body"]
            if tracking_data.get("tracking_pixel"):
                html_content += tracking_data["tracking_pixel"]
                print(f"📊 Added open tracking pixel: {tracking_data.get('pixel_url')}")
            
            # Generate plain text content from HTML (fallback)
            import re
            text_content = re.sub('<[^<]+?>', '', template_data["html_body"])  # Simple HTML strip
            text_content = text_content.strip() or "Please view this email in HTML format."
            
            # Add unsubscribe link to text version
            if tracking_data.get("unsubscribe_url"):
                text_content += f"\n\nUnsubscribe: {tracking_data['unsubscribe_url']}"
            
            # Check if we should use Gmail API
            user_data = get_campaign_owner(campaign_id)
            use_gmail = user_data and user_data.get('gmail_enabled') and user_data.get('google_connected')
            
            if use_gmail:
                print(f"📤 Sending via Gmail API for {email}")
                
                def _do_gmail_send():
                    success, result = send_gmail(
                        user_data=user_data,
                        recipient_email=email,
                        subject=template_data["subject"],
                        html_body=html_content,
                        text_body=text_content
                    )
                    if not success:
                        raise Exception(f"Gmail Send Failed: {result}")
                    return result

                message_id = exponential_backoff_retry(
                    _do_gmail_send,
                    max_retries=3,
                    base_delay=1.0
                )
                print(f"✅ Email sent successfully via Gmail API: {message_id}")
            else:
                # Send email via SES with enhanced tracking and retry logic
                ses_response = exponential_backoff_retry(
                    lambda: ses.send_email(
                        Source=f"{msg_template_data.get('from_name', 'Sentinel')} <{msg_template_data.get('from_email', FROM)}>",
                        Destination={"ToAddresses": [email]},
                        Message={
                            "Subject": {"Data": template_data["subject"]},
                            "Body": {
                                "Html": {"Data": html_content},
                                "Text": {"Data": text_content}
                            }
                        },
                        Tags=[
                            {"Name": "campaign_id", "Value": str(campaign_id)},
                            {"Name": "recipient_id", "Value": str(recipient_id)},
                            {"Name": "cta_count", "Value": str(len(cta_links))}
                        ]
                    ),
                    max_retries=3,
                    base_delay=1.0
                )
                message_id = ses_response.get("MessageId", "unknown")
            status = DeliveryStatus.SENT.value
            
            print(f"✅ Email sent successfully to {email}")
            print(f"📨 SES Message ID: {message_id}")
            print(f"📊 Tracking method: {tracking_data.get('tracking_method', 'None')}")
            
        except Exception as e:
            status = DeliveryStatus.FAILED.value
            
            # Classify error type for better debugging
            error_type = "PERMANENT" if not is_retryable_error(e) else "TRANSIENT"
            error_code = getattr(e, 'response', {}).get('Error', {}).get('Code', type(e).__name__)
            
            print(f"❌ [{error_type}] Failed to send email to {email}: {error_code} - {str(e)}")


        # Record email send status in events table
        update_email_status_in_events(campaign_id, email, status)

    return {"statusCode": 200, "body": json.dumps({"processed": len(event.get('Records', []))})}

def get_campaign_owner(campaign_id):
    """Fetch user record for the campaign owner"""
    try:
        campaigns_table = get_campaigns_table()
        resp = campaigns_table.get_item(Key={'id': str(campaign_id)})
        campaign = resp.get('Item')
        if not campaign:
            return None
            
        owner_id = campaign.get('owner_id')
        if not owner_id:
            return None
            
        users_table = get_users_table()
        resp = users_table.get_item(Key={'id': owner_id})
        return resp.get('Item')
    except Exception as e:
        print(f"Error fetching campaign owner: {e}")
        return None
