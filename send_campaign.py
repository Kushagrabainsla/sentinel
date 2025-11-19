#!/usr/bin/env python3
"""
Simple Sentinel Campaign Trigger
Usage: python send_campaign.py [immediate|scheduled]
"""

import sys
import json
import requests
from datetime import datetime, timedelta
import subprocess
import os

def get_api_url():
    """Get API URL from Terraform outputs or use default"""
    try:
        # Try to get from Terraform
        if os.path.exists('infra'):
            os.chdir('infra')
            result = subprocess.run(['terraform', 'output', '-raw', 'custom_domain_url'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                os.chdir('..')
                return result.stdout.strip()
            
            result = subprocess.run(['terraform', 'output', '-raw', 'api_url'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                os.chdir('..')
                return result.stdout.strip()
            os.chdir('..')
    except:
        pass
    
    # Fallback to custom domain
    return "https://api.thesentinel.site"

def main():
    TARGET_EMAIL = "kushagra.bainsla@sjsu.edu"
    
    # Get campaign type from command line
    campaign_type = sys.argv[1] if len(sys.argv) > 1 else "immediate"
    
    print("🚀 Sentinel Campaign Trigger")
    print("=" * 30)
    print(f"Target: {TARGET_EMAIL}")
    print(f"Mode: {campaign_type}")
    print()
    
    # Validate input
    if campaign_type not in ["immediate", "scheduled"]:
        print(f"❌ Invalid mode: {campaign_type}")
        print("Usage: python send_campaign.py [immediate|scheduled]")
        print()
        print("Examples:")
        print("  python send_campaign.py immediate   # Send now")
        print("  python send_campaign.py scheduled   # Send in 5 minutes")
        sys.exit(1)
    
    # Get API URL
    api_url = get_api_url()
    print(f"🌐 API: {api_url}")
    print()
    
    # Generate unique campaign identifier
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    campaign_id = f"{campaign_type}-{timestamp}"
    print(f"📋 Campaign ID: {campaign_id}")
    
    # Prepare campaign payload
    payload = {
        "name": f"Production Test - {campaign_type} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "subject": f"🚀 Production Campaign Test - {campaign_type}",
        "html_body": f"""
        <html>
        <body style='font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;'>
            <h2>🚀 Campaign Test - {campaign_type}</h2>
            <p>Hello! This is a production test of the Sentinel email system.</p>
            <div style='background: #f0f9ff; padding: 15px; border-radius: 8px; margin: 20px 0;'>
                <h3>📊 Details</h3>
                <ul>
                    <li><strong>Mode:</strong> {campaign_type}</li>
                    <li><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</li>
                    <li><strong>Campaign:</strong> {campaign_id}</li>
                </ul>
            </div>
            <p>
                <a href='https://example.com/test' 
                   style='background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;'>
                   Test Link
                </a>
            </p>
            <p>✅ Campaign system is working correctly!</p>
        </body>
        </html>
        """,
        "text_body": f"""🚀 Campaign Test - {campaign_type}

Hello! This is a production test of the Sentinel email system.

📊 Details:
- Mode: {campaign_type}
- Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
- Campaign: {campaign_id}

Test Link: https://example.com/test

✅ Campaign system is working correctly!""",
        "from_email": "no-reply@thesentinel.site",
        "from_name": "Sentinel Test",
        "segment_id": "all_active",
        "tracking_mode": "smart"
    }
    
    # Add scheduling if needed
    if campaign_type == "scheduled":
        # Schedule for 5 minutes from now
        schedule_time = datetime.utcnow() + timedelta(minutes=5)
        payload["schedule_at"] = schedule_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        print(f"⏰ Scheduled for: {schedule_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    else:
        print("⚡ Sending immediately")
    
    # Create campaign
    print()
    print("🎯 Creating campaign...")
    
    try:
        response = requests.post(
            f"{api_url}/v1/campaigns",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        print()
        if response.status_code in [200, 201]:
            print("✅ SUCCESS! Campaign created")
            print(f"📋 Response: {response.text}")
            
            if campaign_type == "immediate":
                print()
                print("⚡ Email processing now - check your inbox in 1-2 minutes")
                print(f"📬 Target: {TARGET_EMAIL}")
            else:
                print()
                schedule_time = datetime.utcnow() + timedelta(minutes=5)
                print(f"⏰ Email scheduled for: {schedule_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                print("📅 Will be sent in 5 minutes")
        else:
            print(f"❌ FAILED - HTTP {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        sys.exit(1)
    
    print()
    print(f"🎯 Done! {campaign_type} campaign triggered successfully. 🚀")

if __name__ == "__main__":
    main()