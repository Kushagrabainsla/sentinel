#!/usr/bin/env python3
"""
Test script for creating a scheduled email campaign via API Gateway.
This script creates a campaign that will be sent in 3 minutes from now.
"""

import json
import requests
from datetime import datetime, timezone, timedelta

# Configuration
API_BASE_URL = "https://api.thesentinel.site"
CREATE_CAMPAIGN_ENDPOINT = f"{API_BASE_URL}/v1/campaigns"
SCHEDULE_DELAY_MINUTES = 3

def create_scheduled_campaign():
    """Create a scheduled email campaign to be sent in 3 minutes via API."""
    
    # Calculate schedule time (3 minutes from now)
    schedule_time = datetime.now(timezone.utc) + timedelta(minutes=SCHEDULE_DELAY_MINUTES)
    schedule_at = schedule_time.isoformat()
    
    # Campaign payload for scheduled sending
    campaign_data = {
        "name": f"Scheduled Test Campaign (+{SCHEDULE_DELAY_MINUTES}min)",
        "subject": "⏰ Scheduled Test Email",
        "html_body": """
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .btn {{ display: inline-block; padding: 12px 24px; background: #28a745; color: white; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
                .btn:hover {{ background: #218838; }}
                .schedule-info {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .footer {{ margin-top: 30px; padding: 20px; background: #f5f5f5; border-radius: 5px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>⏰ Hello from Sentinel Scheduler!</h2>
                <p>This is a scheduled test email sent through the API Gateway.</p>
                
                <div class="schedule-info">
                    <p><strong>📅 Campaign created at:</strong> {created_at}</p>
                    <p><strong>⏰ Scheduled to send at:</strong> {scheduled_at}</p>
                    <p><strong>🎯 Execution:</strong> EventBridge Scheduler triggered this email automatically!</p>
                </div>
                
                <h3>📊 Test Link Tracking:</h3>
                <p>Click these links to test the scheduled campaign click tracking:</p>
                
                <a href="https://github.com/Kushagrabainsla/sentinel/actions" class="btn">🔄 GitHub Actions</a>
                <a href="https://console.aws.amazon.com/events/home#/rules" class="btn">⏰ EventBridge Rules</a>
                
                <p>Additional tracking test links:</p>
                <ul>
                    <li><a href="https://api.thesentinel.site/events/scheduled-test">📈 Scheduled Campaign Events</a></li>
                    <li><a href="https://console.aws.amazon.com/scheduler/home">🕐 EventBridge Scheduler</a></li>
                    <li><a href="https://console.aws.amazon.com/cloudwatch/home#logStream:group=/aws/lambda/sentinel-start-campaign">📋 Start Campaign Logs</a></li>
                    <li><a href="https://thesentinel.site">🏠 Sentinel Homepage</a></li>
                </ul>
                
                <div class="footer">
                    <p>⏰✅ If you received this email, the scheduled campaign flow is working correctly!</p>
                    <p>🔍 <strong>Email Open Tracking:</strong> Automatically tracked when you view this email</p>
                    <p>🖱️ <strong>Click Tracking:</strong> All links above are tracked for analytics</p>
                    <p>⏱️ <strong>Scheduler Test:</strong> This email was sent via EventBridge Scheduler</p>
                    <p><a href="{{{{unsubscribe_url}}}}">Unsubscribe from future test emails</a></p>
                </div>
            </div>
        </body>
        </html>
        """.format(
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            scheduled_at=schedule_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        ),
        "text_body": f"Hello from Sentinel Scheduler! This is a scheduled test email.\n\nSchedule Info:\n- Created at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n- Scheduled for: {schedule_time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n- Execution: EventBridge Scheduler\n\nTest Links (click tracking enabled):\n- GitHub Actions: https://github.com/Kushagrabainsla/sentinel/actions\n- EventBridge Rules: https://console.aws.amazon.com/events/home#/rules\n- Scheduled Events: https://api.thesentinel.site/events/scheduled-test\n- EventBridge Scheduler: https://console.aws.amazon.com/scheduler/home\n- Start Campaign Logs: https://console.aws.amazon.com/cloudwatch/\n- Sentinel Homepage: https://thesentinel.site\n\nIf you received this, the scheduled campaign flow is working correctly!",
        "from_email": "no-reply@thesentinel.site",
        "from_name": "Sentinel Scheduler",
        "segment_id": "all_active",
        "schedule_at": schedule_at  # Schedule for 3 minutes from now
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"📅 Creating scheduled campaign: {campaign_data['name']}")
        print(f"   Subject: {campaign_data['subject']}")
        print(f"   Current time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"   Scheduled for: {schedule_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"   Delay: {SCHEDULE_DELAY_MINUTES} minutes")
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
            
            if response_data.get('auto_scheduler'):
                print(f"   ⏰ EventBridge scheduler created successfully!")
                print(f"   📬 Email will be sent automatically in {SCHEDULE_DELAY_MINUTES} minutes")
            else:
                print(f"   ⚠️  Campaign created but scheduler setup failed")
                
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
    print("=" * 70)
    print("⏰ SCHEDULED CAMPAIGN TEST (3 MINUTES DELAY)")
    print("=" * 70)
    
    success = create_scheduled_campaign()
    
    if success:
        print(f"\n✅ Test completed successfully!")
        print(f"💡 Campaign will be automatically sent in {SCHEDULE_DELAY_MINUTES} minutes.")
        print(f"💡 Check your email and CloudWatch logs after the scheduled time.")
        print(f"💡 You can also check EventBridge Scheduler in AWS Console.")
    else:
        print("\n❌ Test failed!")
        print("💡 Check network connectivity and API Gateway endpoint.")
    
    print("\n" + "=" * 70)