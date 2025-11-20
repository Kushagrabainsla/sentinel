#!/usr/bin/env python3
"""
Comprehensive scheduled campaign testing using both segments and email lists.
This script creates segments via API and tests both targeting approaches for scheduled campaigns.
All operations use API calls only (no AWS CLI).
"""

import json
import requests
import time
import uuid
from datetime import datetime, timezone, timedelta

# Configuration
API_BASE_URL = "https://api.thesentinel.site"
CAMPAIGNS_ENDPOINT = f"{API_BASE_URL}/v1/campaigns"
SEGMENTS_ENDPOINT = f"{API_BASE_URL}/v1/segments"
SCHEDULE_DELAY_MINUTES = 2  # Schedule campaigns 2 minutes from now

def create_test_segment(name, emails):
    """Create a test segment via API"""
    segment_data = {
        "name": name,
        "description": f"Test segment created for scheduled campaign testing - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "emails": emails
    }
    
    try:
        print(f"📁 Creating test segment: {name}")
        print(f"   Emails: {', '.join(emails)}")
        
        response = requests.post(
            SEGMENTS_ENDPOINT,
            headers={"Content-Type": "application/json"},
            json=segment_data,
            timeout=30
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Segment created successfully!")
            print(f"   Full response: {json.dumps(result, indent=2)}")
            
            # Extract segment ID from the correct response structure
            segment_id = result.get('segment', {}).get('id')
            if not segment_id:
                print(f"⚠️  Warning: Could not extract segment_id from response")
                print(f"   Available keys in result: {list(result.keys())}")
                if 'segment' in result:
                    print(f"   Available keys in segment: {list(result['segment'].keys())}")
            
            print(f"   Segment ID: {segment_id}")
            print(f"   Message: {result.get('message')}")
            return segment_id
        else:
            print(f"❌ Failed to create segment. Status: {response.status_code}")
            print(f"   Response: {response.text}")
            try:
                error_detail = response.json()
                print(f"   Error details: {json.dumps(error_detail, indent=2)}")
            except:
                pass
            return None
            
    except Exception as e:
        print(f"❌ Error creating segment: {str(e)}")
        return None

def create_scheduled_campaign_with_segment(segment_id):
    """Create a scheduled campaign using a segment"""
    
    # Calculate schedule time
    schedule_time = datetime.now(timezone.utc) + timedelta(minutes=SCHEDULE_DELAY_MINUTES)
    schedule_at = int(schedule_time.timestamp())
    
    campaign_data = {
        "name": f"Scheduled Segment Test - {datetime.now().strftime('%H:%M:%S')}",
        "subject": "⏰ Scheduled Campaign via Segment",
        "type": "S",
        "html_body": f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .schedule-info {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #ffc107; }}
                .segment-info {{ background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #28a745; }}
                .btn {{ display: inline-block; padding: 12px 24px; background: #ffc107; color: #212529; text-decoration: none; border-radius: 5px; margin: 10px 5px; font-weight: bold; }}
                .footer {{ margin-top: 30px; padding: 20px; background: #f5f5f5; border-radius: 5px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>⏰ Scheduled Campaign via Segment</h2>
                <p>This is a scheduled campaign sent using a <strong>segment-based approach</strong>!</p>
                
                <div class="schedule-info">
                    <h3>⏰ Schedule Details:</h3>
                    <p><strong>Created At:</strong> {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
                    <p><strong>Scheduled For:</strong> {schedule_time.strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
                    <p><strong>Delay:</strong> {SCHEDULE_DELAY_MINUTES} minutes</p>
                    <p><strong>Scheduler:</strong> EventBridge Scheduler</p>
                </div>
                
                <div class="segment-info">
                    <h3>📁 Segment Details:</h3>
                    <p><strong>Segment ID:</strong> {segment_id}</p>
                    <p><strong>Campaign Type:</strong> Scheduled (S)</p>
                    <p><strong>Targeting Method:</strong> Segment-based targeting</p>
                </div>
                
                <h3>📊 Test Links:</h3>
                <a href="https://github.com/Kushagrabainsla/sentinel" class="btn">📂 Project Repository</a>
                <a href="https://api.thesentinel.site/v1/segments/{segment_id}" class="btn">📁 View Segment</a>
                <a href="https://console.aws.amazon.com/scheduler/home" class="btn">⏰ EventBridge Scheduler</a>
                
                <div class="footer">
                    <p>⏰✅ If you received this email, scheduled segment-based campaigns are working!</p>
                    <p>📁 <strong>Segment Targeting:</strong> This campaign used segment_id for recipient targeting</p>
                    <p>⏰ <strong>Scheduled Execution:</strong> Campaign was automatically triggered by EventBridge Scheduler</p>
                    <p>🔍 <strong>Tracking:</strong> Opens and clicks are tracked for analytics</p>
                    <p><a href="{{{{unsubscribe_url}}}}">Unsubscribe</a></p>
                </div>
            </div>
        </body>
        </html>
        """,
        "from_email": "no-reply@thesentinel.site",
        "from_name": "Sentinel Scheduled Test",
        "segment_id": segment_id,
        "schedule_at": schedule_at
    }
    
    return send_campaign_request(campaign_data, "Segment-Based", schedule_time)

def create_scheduled_campaign_with_emails():
    """Create a scheduled campaign using email list"""
    
    # Calculate schedule time
    schedule_time = datetime.now(timezone.utc) + timedelta(minutes=SCHEDULE_DELAY_MINUTES)
    schedule_at = int(schedule_time.timestamp())
    
    test_emails = [
        'kushagra.bainsla+email1@sjsu.edu',
        'kushagra.bainsla+email2@sjsu.edu'
    ]
    
    campaign_data = {
        "name": f"Scheduled Email List Test - {datetime.now().strftime('%H:%M:%S')}",
        "subject": "📧⏰ Scheduled Campaign via Email List",
        "type": "S",
        "html_body": f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .schedule-info {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #ffc107; }}
                .email-info {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #2196f3; }}
                .btn {{ display: inline-block; padding: 12px 24px; background: #2196f3; color: white; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
                .footer {{ margin-top: 30px; padding: 20px; background: #f5f5f5; border-radius: 5px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>📧⏰ Scheduled Campaign via Email List</h2>
                <p>This is a scheduled campaign sent using a <strong>direct email list approach</strong>!</p>
                
                <div class="schedule-info">
                    <h3>⏰ Schedule Details:</h3>
                    <p><strong>Created At:</strong> {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
                    <p><strong>Scheduled For:</strong> {schedule_time.strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
                    <p><strong>Delay:</strong> {SCHEDULE_DELAY_MINUTES} minutes</p>
                    <p><strong>Scheduler:</strong> EventBridge Scheduler</p>
                </div>
                
                <div class="email-info">
                    <h3>📧 Email List Details:</h3>
                    <p><strong>Recipients:</strong> {len(test_emails)} emails</p>
                    <p><strong>Email List:</strong> {', '.join(test_emails)}</p>
                    <p><strong>Campaign Type:</strong> Scheduled (S)</p>
                    <p><strong>Targeting Method:</strong> Direct email list targeting</p>
                </div>
                
                <h3>📊 Test Links:</h3>
                <a href="https://github.com/Kushagrabainsla/sentinel" class="btn">📂 Project Repository</a>
                <a href="https://api.thesentinel.site/v1/campaigns" class="btn">📊 View Campaigns</a>
                <a href="https://console.aws.amazon.com/scheduler/home" class="btn">⏰ EventBridge Scheduler</a>
                
                <div class="footer">
                    <p>📧⏰✅ If you received this email, scheduled email list campaigns are working!</p>
                    <p>📧 <strong>Email List Targeting:</strong> This campaign used direct email list for recipients</p>
                    <p>⏰ <strong>Scheduled Execution:</strong> Campaign was automatically triggered by EventBridge Scheduler</p>
                    <p>🔍 <strong>Tracking:</strong> Opens and clicks are tracked for analytics</p>
                    <p><a href="{{{{unsubscribe_url}}}}">Unsubscribe</a></p>
                </div>
            </div>
        </body>
        </html>
        """,
        "from_email": "no-reply@thesentinel.site",
        "from_name": "Sentinel Scheduled Test",
        "emails": test_emails,
        "schedule_at": schedule_at
    }
    
    return send_campaign_request(campaign_data, "Email List", schedule_time)

def send_campaign_request(campaign_data, approach_name, schedule_time):
    """Send campaign creation request"""
    try:
        print(f"📧 Creating {approach_name} scheduled campaign: {campaign_data['name']}")
        print(f"   Subject: {campaign_data['subject']}")
        print(f"   Current time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"   Scheduled for: {schedule_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"   Delay: {SCHEDULE_DELAY_MINUTES} minutes")
        
        if 'segment_id' in campaign_data:
            print(f"   Targeting: Segment ID {campaign_data['segment_id']}")
        elif 'emails' in campaign_data:
            print(f"   Targeting: {len(campaign_data['emails'])} email addresses")
        
        response = requests.post(
            CAMPAIGNS_ENDPOINT,
            headers={"Content-Type": "application/json"},
            json=campaign_data,
            timeout=30
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ {approach_name} campaign created successfully!")
            print(f"   Full response: {json.dumps(result, indent=2)}")
            print(f"   Campaign ID: {result.get('campaign_id')}")
            print(f"   State: {result.get('state')}")
            
            if result.get('auto_scheduler'):
                print(f"   ⏰ EventBridge scheduler created successfully!")
                print(f"   📬 Email will be sent automatically in {SCHEDULE_DELAY_MINUTES} minutes")
            
            if 'segment_id' in result and 'emails' in campaign_data:
                print(f"   📁 Temporary segment created: {result.get('segment_id')}")
            
            return result
        else:
            print(f"❌ {approach_name} campaign failed. Status: {response.status_code}")
            print(f"   Response: {response.text}")
            try:
                error_detail = response.json()
                print(f"   Error details: {json.dumps(error_detail, indent=2)}")
            except:
                pass
            return None
            
    except Exception as e:
        print(f"❌ Error creating {approach_name} campaign: {str(e)}")
        return None

def cleanup_test_segment(segment_id):
    """Clean up test segment after testing"""
    if not segment_id:
        print("🧹 No segment ID to clean up")
        return
        
    try:
        print(f"🧹 Cleaning up test segment: {segment_id}")
        
        # First, verify the segment exists
        check_response = requests.get(
            f"{SEGMENTS_ENDPOINT}/{segment_id}",
            timeout=30
        )
        
        if check_response.status_code == 404:
            print(f"✅ Segment already deleted or never existed: {segment_id}")
            return
        elif check_response.status_code != 200:
            print(f"⚠️  Could not verify segment existence (Status: {check_response.status_code})")
            print(f"   Response: {check_response.text}")
        else:
            print(f"📁 Segment exists, proceeding with deletion...")
        
        # Attempt to delete the segment
        response = requests.delete(
            f"{SEGMENTS_ENDPOINT}/{segment_id}",
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"✅ Test segment cleaned up successfully")
        elif response.status_code == 404:
            print(f"✅ Segment was already deleted: {segment_id}")
        else:
            print(f"⚠️  Could not clean up segment (Status: {response.status_code})")
            print(f"   Response: {response.text}")
            try:
                error_detail = response.json()
                print(f"   Error details: {json.dumps(error_detail, indent=2)}")
            except:
                pass
            print(f"   You may need to manually delete segment: {segment_id}")
            
    except Exception as e:
        print(f"⚠️  Error cleaning up segment: {str(e)}")

def main():
    """Main test function"""
    print("=" * 80)
    print("⏰ COMPREHENSIVE SCHEDULED CAMPAIGN TESTS")
    print("=" * 80)
    print("Testing both segment-based and email list approaches for scheduled campaigns")
    print(f"All campaigns will be scheduled for {SCHEDULE_DELAY_MINUTES} minutes from now")
    print("All operations performed via API calls (no AWS CLI)")
    print()
    
    # Test 1: Segment-based scheduled campaign
    print("🎯 TEST 1: SCHEDULED CAMPAIGN WITH SEGMENT")
    print("-" * 50)
    
    # Create test segment
    test_segment_emails = [
        "kushagra.bainsla+segment1@sjsu.edu",
        "kushagra.bainsla+segment2@sjsu.edu"
    ]
    
    segment_id = create_test_segment("Scheduled-Test-Segment", test_segment_emails)
    
    if segment_id:
        # Wait a moment for segment to be ready
        print("⏳ Waiting 2 seconds for segment to be ready...")
        time.sleep(2)
        
        # Verify segment was created and is accessible
        try:
            verify_response = requests.get(f"{SEGMENTS_ENDPOINT}/{segment_id}", timeout=30)
            if verify_response.status_code == 200:
                print("✅ Segment verified and ready for campaign creation")
            else:
                print(f"⚠️  Segment verification failed (Status: {verify_response.status_code})")
        except Exception as e:
            print(f"⚠️  Could not verify segment: {e}")
        
        # Create campaign with segment
        segment_campaign = create_scheduled_campaign_with_segment(segment_id)
        
        if segment_campaign:
            print("✅ Segment-based scheduled campaign test completed!")
        else:
            print("❌ Segment-based scheduled campaign test failed!")
    else:
        print("❌ Could not create test segment, skipping segment-based test")
    
    print()
    
    # Test 2: Email list scheduled campaign
    print("📧 TEST 2: SCHEDULED CAMPAIGN WITH EMAIL LIST")
    print("-" * 50)
    
    email_campaign = create_scheduled_campaign_with_emails()
    
    if email_campaign:
        print("✅ Email list scheduled campaign test completed!")
    else:
        print("❌ Email list scheduled campaign test failed!")
    
    print()
    
    # Summary
    print("=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    if segment_id and segment_campaign:
        print("✅ Segment-based scheduled campaign: PASSED")
    else:
        print("❌ Segment-based scheduled campaign: FAILED")
    
    if email_campaign:
        print("✅ Email list scheduled campaign: PASSED")
    else:
        print("❌ Email list scheduled campaign: FAILED")
    
    print()
    print(f"⏰ Campaigns are scheduled to send in {SCHEDULE_DELAY_MINUTES} minutes")
    print("💡 Check your email inbox after the scheduled time to verify delivery")
    print("💡 Monitor CloudWatch logs and EventBridge Scheduler for execution details")
    print("💡 You can check EventBridge Scheduler in AWS Console to see the scheduled rules")
    
    # Cleanup
    if segment_id:
        print()
        cleanup_test_segment(segment_id)
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    main()