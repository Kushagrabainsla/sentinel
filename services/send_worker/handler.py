import json
import os
import re
import boto3
from common_db import update_recipient_status
from tracking import generate_tracking_data

ses = boto3.client("ses")
FROM = os.environ.get("SES_FROM_ADDRESS")       # set in Terraform
TEMPLATE = os.environ.get("SES_TEMPLATE_ARN")   # set in Terraform (name is fine)

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
        r'terms',
        r'privacy',
        r'policy',
        r'unsubscribe',
        r'footer',
        r'mailto:',
        r'#',  # anchor links
        r'javascript:',  # javascript links
    ]
    
    for i, (url, link_text) in enumerate(matches):
        # Skip excluded links
        should_exclude = any(re.search(pattern, url.lower()) or re.search(pattern, link_text.lower()) 
                           for pattern in excluded_patterns)
        
        if not should_exclude and url.startswith(('http://', 'https://')):
            cta_id = f"cta_link_{i+1}"
            cta_links[cta_id] = url
    
    return cta_links

def lambda_handler(event, _context):
    """
    Triggered by SQS event. Each record has body:
    {"campaign_id":123, "recipient_id":456, "email":"user@example.com"}
    """
    for rec in event.get("Records", []):
        body = json.loads(rec["body"])
        campaign_id = body["campaign_id"]
        recipient_id = body["recipient_id"]
        email = body["email"]

        try:
            # Get template data from the message
            msg_template_data = body.get("template_data", {})
            html_body = msg_template_data.get("html_body", "")
            
            # Extract CTA links from HTML content
            cta_links = extract_cta_links(html_body)
            
            # Generate tracking data for analytics (only for extracted CTAs)
            tracking_data = generate_tracking_data(
                campaign_id=campaign_id, 
                recipient_id=recipient_id, 
                email=email,
                cta_links=cta_links
            )
            
            # Replace original CTA links with tracking links in HTML
            processed_html = html_body
            for cta_id, original_url in cta_links.items():
                if cta_id in tracking_data["tracked_cta_links"]:
                    tracking_url = tracking_data["tracked_cta_links"][cta_id]
                    processed_html = processed_html.replace(original_url, tracking_url)
            
            # Prepare template data for SES
            template_data = {
                "name": email.split("@")[0],
                "subject": msg_template_data.get("subject", "Newsletter"),
                "html_body": processed_html,
                "text_body": msg_template_data.get("text_body", ""),
                "tracking_pixel_url": tracking_data["tracking_pixel_url"],
                "unsubscribe_url": tracking_data["unsubscribe_url"]
            }
            
            print(f"📧 Sending tracked email to {email} for campaign {campaign_id}")
            print(f"🎯 CTA links tracked: {list(tracking_data['tracked_cta_links'].keys())}")
            
            # Prepare email content with tracking pixel
            html_content = template_data["html_body"]
            if template_data["tracking_pixel_url"]:
                # Add tracking pixel at the end of HTML body
                tracking_pixel = f'<img src="{template_data["tracking_pixel_url"]}" width="1" height="1" style="display:none;">'
                html_content += tracking_pixel
            
            # Send email via SES with processed content
            ses.send_email(
                Source=f"{msg_template_data.get('from_name', 'Sentinel')} <{msg_template_data.get('from_email', FROM)}>",
                Destination={"ToAddresses": [email]},
                Message={
                    "Subject": {"Data": template_data["subject"]},
                    "Body": {
                        "Html": {"Data": html_content},
                        "Text": {"Data": template_data["text_body"]}
                    }
                },
                Tags=[
                    {"Name": "campaign_id", "Value": str(campaign_id)},
                    {"Name": "recipient_id", "Value": str(recipient_id)}
                ]
            )
            status = "sent"
            print(f"✅ Successfully sent tracked email to {email}")
            
        except Exception as e:
            status = "failed"
            print(f"❌ Failed to send email to {email}: {e}")

        # Update recipient status
        update_recipient_status(campaign_id, recipient_id, status)

    return {"statusCode": 200, "body": json.dumps({"processed": len(event.get('Records', []))})}
