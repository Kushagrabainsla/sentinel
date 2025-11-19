#!/usr/bin/env python3
"""
Test script for creating an immediate email campaign via API Gateway.
This script creates a campaign that will be sent immediately.
"""

import json
import requests
from datetime import datetime, timezone

# Configuration
API_BASE_URL = "https://api.thesentinel.site"
CREATE_CAMPAIGN_ENDPOINT = f"{API_BASE_URL}/v1/campaigns"

def create_immediate_campaign():
    """Create and trigger an immediate email campaign via API."""
    
    # Campaign payload for immediate sending
    campaign_data = {
        "name": "Immediate Test Campaign",
        "subject": "🚀 Immediate Test Email",
        "html_body": """
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .btn {{ display: inline-block; padding: 12px 24px; background: #007cba; color: white; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
                .btn:hover {{ background: #005a87; }}
                .footer {{ margin-top: 30px; padding: 20px; background: #f5f5f5; border-radius: 5px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>🚀 Hello from Sentinel!</h2>
                <p>This is an immediate test email sent through the API Gateway.</p>
                <p><strong>Sent at:</strong> {timestamp}</p>
                
                <h3>📊 Test Link Tracking:</h3>
                <p>Click these links to test the click tracking functionality:</p>
                
                <a href="https://github.com/Kushagrabainsla/sentinel" class="btn">📂 View Project Repository</a>
                <a href="https://docs.aws.amazon.com/ses/" class="btn">📖 AWS SES Documentation</a>
                
                <p>You can also test these inline links:</p>
                <ul>
                    <li><a href="https://api.thesentinel.site/events/test">📈 Check Campaign Events</a></li>
                    <li><a href="https://console.aws.amazon.com/dynamodb">💾 View DynamoDB Tables</a></li>
                    <li><a href="https://console.aws.amazon.com/cloudwatch/home#logStream:group=/aws/lambda/sentinel-create-campaign">📋 CloudWatch Logs</a></li>
                </ul>
                
                <div class="footer">
                    <p>✅ If you received this email, the immediate campaign flow is working correctly!</p>
                    <p>🔍 <strong>Email Open Tracking:</strong> Automatically tracked when you view this email</p>
                    <p>🖱️ <strong>Click Tracking:</strong> All links above are tracked for analytics</p>
                    <p><a href="{{{{unsubscribe_url}}}}">Unsubscribe from future test emails</a></p>
                </div>
            </div>
        </body>
        </html>
        """.format(timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")),
        "text_body": "Hello from Sentinel! This is an immediate test email sent at {timestamp}.\n\nTest Links (click tracking enabled):\n- Project Repository: https://github.com/Kushagrabainsla/sentinel\n- AWS SES Docs: https://docs.aws.amazon.com/ses/\n- Campaign Events: https://api.thesentinel.site/events/test\n- DynamoDB Console: https://console.aws.amazon.com/dynamodb\n- CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/\n\nIf you received this, the immediate campaign flow is working correctly!".format(timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")),
        "from_email": "no-reply@thesentinel.site",
        "from_name": "Sentinel Test",
        "segment_id": "all_active",
        # No schedule_at means immediate execution (defaults to now)
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"📧 Creating immediate campaign: {campaign_data['name']}")
        print(f"   Subject: {campaign_data['subject']}")
        print(f"   Expected execution: Immediate (within 60 seconds)")
        print(f"   API Endpoint: {CREATE_CAMPAIGN_ENDPOINT}")
        
        # Make HTTP POST request to API Gateway
        response = requests.post(
            CREATE_CAMPAIGN_ENDPOINT,
            headers=headers,
            json=campaign_data,
            timeout=30
        )
        
        # Parse the response
        if response.status_code == 201:
            response_data = response.json()
            print(f"✅ Campaign created successfully!")
            print(f"   Campaign ID: {response_data.get('campaign_id')}")
            print(f"   State: {response_data.get('state')}")
            print(f"   Execution Path: {response_data.get('execution_path')}")
            print(f"   Scheduled At: {response_data.get('schedule_at')}")
            
            if response_data.get('triggered'):
                print(f"   ⚡ Campaign triggered for immediate execution!")
            else:
                print(f"   ⚠️  Campaign created but immediate trigger failed")
                
        else:
            print(f"❌ Failed to create campaign. Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP request error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error creating campaign: {str(e)}")
        return False
        
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 IMMEDIATE CAMPAIGN TEST")
    print("=" * 60)
    
    success = create_immediate_campaign()
    
    if success:
        print("\n✅ Test completed successfully!")
        print("💡 Check your email and CloudWatch logs to verify the campaign was processed.")
    else:
        print("\n❌ Test failed!")
        print("💡 Check network connectivity and API Gateway endpoint.")
    
    print("\n" + "=" * 60)