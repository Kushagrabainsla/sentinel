import json
import os
import re
import boto3
from common_db import update_recipient_status
from tracking import generate_tracking_data

ses = boto3.client("ses")
FROM = os.environ.get("SES_FROM_ADDRESS")       # set in Terraform
TEMPLATE = os.environ.get("SES_TEMPLATE_ARN")   # set in Terraform (name is fine)

# Enhanced tracking configuration
TRACKING_MODE = os.environ.get("TRACKING_MODE", "smart")  # smart, inline, external, disabled

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
        email = body["email"]

        try:
            # Get template data from the message
            msg_template_data = body.get("template_data", {})
            html_body = msg_template_data.get("html_body", "")
            
            # Check for custom tracking mode in the message, fallback to environment variable
            tracking_mode = body.get("tracking_mode", TRACKING_MODE)
            
            print(f"📧 Processing email for {email} (Campaign: {campaign_id})")
            print(f"🎯 Tracking mode: {tracking_mode}")
            
            # Extract CTA links from HTML content (if tracking enabled)
            cta_links = {}
            if tracking_mode != "disabled":
                cta_links = extract_cta_links(html_body)
                if cta_links:
                    print(f"🔗 Found {len(cta_links)} CTA links to track")
            
            # Generate enhanced tracking data with specified mode
            tracking_data = generate_tracking_data(
                campaign_id=campaign_id, 
                recipient_id=recipient_id, 
                email=email,
                cta_links=cta_links,
                tracking_mode=tracking_mode
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
            
            # Prepare template data for SES
            template_data = {
                "name": email.split("@")[0],
                "subject": msg_template_data.get("subject", "Newsletter"),
                "html_body": processed_html,
                "text_body": msg_template_data.get("text_body", ""),
            }
            
            print(f"📧 Sending email to {email} for campaign {campaign_id}")
            if tracking_data.get("tracked_cta_links"):
                print(f"🎯 CTA links tracked: {list(tracking_data['tracked_cta_links'].keys())}")
            
            # Add tracking pixel using enhanced method
            html_content = template_data["html_body"]
            if tracking_data.get("tracking_pixel_html"):
                # Find best insertion point for tracking pixel
                if "</body>" in html_content.lower():
                    # Insert before closing body tag
                    html_content = html_content.replace("</body>", f"{tracking_data['tracking_pixel_html']}</body>")
                elif "</html>" in html_content.lower():
                    # Insert before closing html tag
                    html_content = html_content.replace("</html>", f"{tracking_data['tracking_pixel_html']}</html>")
                else:
                    # Append to end
                    html_content += tracking_data["tracking_pixel_html"]
                
                print(f"📊 Added tracking pixel using method: {tracking_data.get('tracking_method', 'Unknown')}")
            
            # Add unsubscribe link to text version if available
            text_content = template_data["text_body"]
            if tracking_data.get("unsubscribe_url") and text_content:
                text_content += f"\n\nUnsubscribe: {tracking_data['unsubscribe_url']}"
            
            # Send email via SES with enhanced tracking
            ses_response = ses.send_email(
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
                    {"Name": "tracking_mode", "Value": tracking_mode},
                    {"Name": "cta_count", "Value": str(len(cta_links))}
                ]
            )
            
            message_id = ses_response.get("MessageId", "unknown")
            status = "sent"
            
            print(f"✅ Email sent successfully to {email}")
            print(f"📨 SES Message ID: {message_id}")
            print(f"📊 Tracking method: {tracking_data.get('tracking_method', 'None')}")
            
        except Exception as e:
            status = "failed"
            print(f"❌ Failed to send email to {email}: {e}")

        # Update recipient status
        update_recipient_status(campaign_id, recipient_id, status)

    return {"statusCode": 200, "body": json.dumps({"processed": len(event.get('Records', []))})}
