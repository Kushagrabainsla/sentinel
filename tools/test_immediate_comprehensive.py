#!/usr/bin/env python3
"""
Comprehensive immediate campaign testing using both segments and email lists.
This script creates a user, authenticates, then creates segments via API and tests 
both targeting approaches for immediate campaigns.
All operations use authenticated API calls only (no AWS CLI).
"""

import json
import requests
import time
import uuid
from datetime import datetime, timezone

# Configuration
API_BASE_URL = "https://api.thesentinel.site"
CAMPAIGNS_ENDPOINT = f"{API_BASE_URL}/v1/campaigns"
SEGMENTS_ENDPOINT = f"{API_BASE_URL}/v1/segments"
AUTH_ENDPOINT = f"{API_BASE_URL}/v1/auth"

# Global API key for authenticated requests
API_KEY = None

def create_test_user():
    """Create a test user and get API key for authentication"""
    global API_KEY
    
    # Generate unique test user email
    test_email = f"test-{int(time.time())}-{uuid.uuid4().hex[:6]}@example.com"
    
    user_data = {
        "email": test_email,
        "password": "TestPassword123!",
        "name": "Test User for Campaign Testing"
    }
    
    print(f"👤 Creating test user: {test_email}")
    
    try:
        response = requests.post(
            f"{AUTH_ENDPOINT}/register",
            headers={"Content-Type": "application/json"},
            json=user_data,
            timeout=30
        )
        
        if response.status_code == 201:
            result = response.json()
            user_data = result.get('user', {})
            API_KEY = user_data.get('api_key')
            if API_KEY:
                print(f"✅ User created successfully! API Key: {API_KEY[:16]}...")
                return API_KEY
            else:
                print(f"❌ No API key found in response: {json.dumps(result, indent=2)}")
                return None
        else:
            print(f"❌ Failed to create user: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating user: {str(e)}")
        return None

def get_auth_headers():
    """Get headers with API key for authenticated requests"""
    if not API_KEY:
        raise ValueError("No API key available. Please create a user first.")
    return {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }

def create_test_segment(name, emails):
    """Create a test segment via authenticated API"""
    segment_data = {
        "name": name,
        "description": f"Test segment created for immediate campaign testing - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "emails": emails
    }
    
    try:
        print(f"📁 Creating test segment: {name}")
        print(f"   Emails: {', '.join(emails)}")
        
        response = requests.post(
            SEGMENTS_ENDPOINT,
            headers=get_auth_headers(),
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

def create_immediate_campaign_with_segment(segment_id):
    """Create an immediate campaign using a segment"""
    campaign_data = {
        "name": f"Immediate Segment Test - {datetime.now().strftime('%H:%M:%S')}",
        "subject": "🎯 Immediate Campaign via Segment",
        "type": "I",
        "html_body": f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .segment-info {{ background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #28a745; }}
                .btn {{ display: inline-block; padding: 12px 24px; background: #28a745; color: white; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
                .footer {{ margin-top: 30px; padding: 20px; background: #f5f5f5; border-radius: 5px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>🎯 Immediate Campaign via Segment</h2>
                <p>This is an immediate campaign sent using a <strong>segment-based approach</strong>!</p>
                
                <div class="segment-info">
                    <h3>📁 Segment Details:</h3>
                    <p><strong>Segment ID:</strong> {segment_id}</p>
                    <p><strong>Campaign Type:</strong> Immediate (I)</p>
                    <p><strong>Targeting Method:</strong> Segment-based targeting</p>
                    <p><strong>Created At:</strong> {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
                </div>
                
                <h3>📊 Test Links:</h3>
                <a href="https://github.com/Kushagrabainsla/sentinel" class="btn">📂 Project Repository</a>
                <a href="https://api.thesentinel.site/v1/segments/{segment_id}" class="btn">📁 View Segment</a>
                
                <div class="footer">
                    <p>✅ If you received this email, immediate segment-based campaigns are working!</p>
                    <p>📁 <strong>Segment Targeting:</strong> This campaign used segment_id for recipient targeting</p>
                    <p>⚡ <strong>Immediate Execution:</strong> Campaign was sent immediately upon creation</p>
                    <p>🔍 <strong>Tracking:</strong> Opens and clicks are tracked for analytics</p>
                    <p><a href="{{{{unsubscribe_url}}}}">Unsubscribe</a></p>
                </div>
            </div>
        </body>
        </html>
        """,
        "from_email": "no-reply@thesentinel.site",
        "from_name": "Sentinel Segment Test",
        "segment_id": segment_id
    }
    
    return send_campaign_request(campaign_data, "Segment-Based")

def create_immediate_campaign_with_emails():
    """Create an immediate campaign using email list"""
    test_emails = [
        'kushagra.bainsla+email1@sjsu.edu',
        'kushagra.bainsla+email2@sjsu.edu'
    ]
    
    campaign_data = {
        "name": f"Immediate Email List Test - {datetime.now().strftime('%H:%M:%S')}",
        "subject": "📧 Immediate Campaign via Email List",
        "type": "I",
        "html_body": f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .email-info {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #2196f3; }}
                .btn {{ display: inline-block; padding: 12px 24px; background: #2196f3; color: white; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
                .footer {{ margin-top: 30px; padding: 20px; background: #f5f5f5; border-radius: 5px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>📧 Immediate Campaign via Email List</h2>
                <p>This is an immediate campaign sent using a <strong>direct email list approach</strong>!</p>
                
                <div class="email-info">
                    <h3>📧 Email List Details:</h3>
                    <p><strong>Recipients:</strong> {len(test_emails)} emails</p>
                    <p><strong>Email List:</strong> {', '.join(test_emails)}</p>
                    <p><strong>Campaign Type:</strong> Immediate (I)</p>
                    <p><strong>Targeting Method:</strong> Direct email list targeting</p>
                    <p><strong>Created At:</strong> {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
                </div>
                
                <h3>📊 Test Links:</h3>
                <a href="https://github.com/Kushagrabainsla/sentinel" class="btn">📂 Project Repository</a>
                <a href="https://api.thesentinel.site/v1/campaigns" class="btn">📊 View Campaigns</a>
                
                <div class="footer">
                    <p>✅ If you received this email, immediate email list campaigns are working!</p>
                    <p>📧 <strong>Email List Targeting:</strong> This campaign used direct email list for recipients</p>
                    <p>⚡ <strong>Immediate Execution:</strong> Campaign was sent immediately upon creation</p>
                    <p>🔍 <strong>Tracking:</strong> Opens and clicks are tracked for analytics</p>
                    <p><a href="{{{{unsubscribe_url}}}}">Unsubscribe</a></p>
                </div>
            </div>
        </body>
        </html>
        """,
        "from_email": "no-reply@thesentinel.site",
        "from_name": "Sentinel Email Test",
        "emails": test_emails
    }
    
    return send_campaign_request(campaign_data, "Email List")

def send_campaign_request(campaign_data, approach_name):
    """Send campaign creation request"""
    try:
        print(f"📧 Creating {approach_name} immediate campaign: {campaign_data['name']}")
        print(f"   Subject: {campaign_data['subject']}")
        if 'segment_id' in campaign_data:
            print(f"   Targeting: Segment ID {campaign_data['segment_id']}")
        elif 'emails' in campaign_data:
            print(f"   Targeting: {len(campaign_data['emails'])} email addresses")
        
        response = requests.post(
            CAMPAIGNS_ENDPOINT,
            headers=get_auth_headers(),
            json=campaign_data,
            timeout=30
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ {approach_name} campaign created successfully!")
            print(f"   Full response: {json.dumps(result, indent=2)}")
            print(f"   Campaign ID: {result.get('campaign_id')}")
            print(f"   State: {result.get('state')}")
            
            if result.get('triggered'):
                print(f"   ⚡ Campaign triggered for immediate execution!")
            
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
    print("🚀 COMPREHENSIVE IMMEDIATE CAMPAIGN TESTS")
    print("=" * 80)
    print("Testing both segment-based and email list approaches for immediate campaigns")
    print("All operations performed via authenticated API calls (no AWS CLI)")
    print()
    
    # Step 0: Create test user and get API key
    print("🔐 AUTHENTICATION SETUP")
    print("-" * 30)
    
    api_key = create_test_user()
    if not api_key:
        print("❌ Failed to create test user. Cannot proceed with tests.")
        return
    
    print(f"✅ Authentication ready. API Key: {api_key[:16]}...")
    print()
    
    # Test 1: Segment-based immediate campaign
    print("🎯 TEST 1: IMMEDIATE CAMPAIGN WITH SEGMENT")
    print("-" * 50)
    
    # Create test segment
    test_segment_emails = [
        "kushagra.bainsla+segment1@sjsu.edu",
        "kushagra.bainsla+segment2@sjsu.edu"
    ]
    
    segment_id = create_test_segment("Immediate-Test-Segment", test_segment_emails)
    
    if segment_id:
        # Wait a moment for segment to be ready
        print("⏳ Waiting 2 seconds for segment to be ready...")
        time.sleep(2)
        
        # Verify segment was created and is accessible
        try:
            verify_response = requests.get(f"{SEGMENTS_ENDPOINT}/{segment_id}", headers=get_auth_headers(), timeout=30)
            if verify_response.status_code == 200:
                print("✅ Segment verified and ready for campaign creation")
            else:
                print(f"⚠️  Segment verification failed (Status: {verify_response.status_code})")
        except Exception as e:
            print(f"⚠️  Could not verify segment: {e}")
        
        # Create campaign with segment
        segment_campaign = create_immediate_campaign_with_segment(segment_id)
        
        if segment_campaign:
            print("✅ Segment-based immediate campaign test completed!")
        else:
            print("❌ Segment-based immediate campaign test failed!")
    else:
        print("❌ Could not create test segment, skipping segment-based test")
    
    print()
    
    # Test 2: Email list immediate campaign
    print("📧 TEST 2: IMMEDIATE CAMPAIGN WITH EMAIL LIST")
    print("-" * 50)
    
    email_campaign = create_immediate_campaign_with_emails()
    
    if email_campaign:
        print("✅ Email list immediate campaign test completed!")
    else:
        print("❌ Email list immediate campaign test failed!")
    
    print()
    
    # Summary
    print("=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    if segment_id and segment_campaign:
        print("✅ Segment-based immediate campaign: PASSED")
    else:
        print("❌ Segment-based immediate campaign: FAILED")
    
    if email_campaign:
        print("✅ Email list immediate campaign: PASSED")
    else:
        print("❌ Email list immediate campaign: FAILED")
    
    print()
    print("💡 Check your email inbox to verify campaigns were sent successfully")
    print("💡 Monitor CloudWatch logs for detailed execution information")
    
    # Cleanup
    if segment_id:
        print()
        cleanup_test_segment(segment_id)
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    main()