#!/usr/bin/env python3
"""
Simple script to check tracking events for your campaigns.
Usage: python3 check_events_api.py [campaign_id]
"""
import requests
import json
import sys
from datetime import datetime, timezone

def get_campaign_events_via_api(campaign_id, api_base_url="https://api.thesentinel.site"):
    """Get events for a campaign via the tracking API"""
    try:
        url = f"{api_base_url}/events/{campaign_id}"
        
        print(f"🔍 Requesting events from: {url}")
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error calling events API: {e}")
        return None

def format_timestamp(timestamp):
    """Format Unix timestamp to readable date"""
    try:
        if isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
        return str(timestamp)
    except:
        return str(timestamp)

def main():
    print("🔍 Checking tracking events...\n")
    
    if len(sys.argv) > 1:
        campaign_id = sys.argv[1]
    else:
        print("💡 Usage: python3 check_events_api.py <campaign_id>")
        print("\nTo get your campaign ID:")
        print("- Check the output when you run: python3 send_campaign.py immediate")
        print("- Look for: 'Campaign created with ID: xxxxxx'\n")
        
        campaign_id = input("Enter campaign ID: ").strip()
        if not campaign_id:
            print("❌ Campaign ID is required")
            return
    
    # Get events via API
    events_data = get_campaign_events_via_api(campaign_id)
    
    if not events_data:
        print("❌ Could not retrieve events data")
        return
    
    print("✅ Successfully retrieved events data!")
    print(f"📊 Campaign ID: {events_data.get('campaign_id')}")
    print(f"📈 Total Events: {events_data.get('total_events', 0)}")
    print()
    
    # Show event summary
    event_summary = events_data.get('event_summary', {})
    if event_summary:
        print("📋 Event Summary:")
        for event_type, count in event_summary.items():
            print(f"   - {event_type}: {count} events")
        print()
    
    # Show recent events
    events = events_data.get('events', [])
    if events:
        print(f"📝 Recent Events (showing up to {len(events)}):")
        
        for i, event in enumerate(events[:10], 1):  # Show first 10
            event_type = event.get('type', 'unknown')
            email = event.get('email', 'unknown')
            timestamp = format_timestamp(event.get('created_at'))
            recipient_id = event.get('recipient_id', 'unknown')
            
            print(f"   {i}. {event_type.upper()} - {email}")
            print(f"      Time: {timestamp}")
            print(f"      Recipient ID: {recipient_id}")
            
            # Show metadata if available
            raw_metadata = event.get('raw')
            if raw_metadata:
                try:
                    metadata = json.loads(raw_metadata)
                    if 'user_agent' in metadata:
                        user_agent = metadata['user_agent'][:50] + '...' if len(metadata['user_agent']) > 50 else metadata['user_agent']
                        print(f"      User Agent: {user_agent}")
                    if 'ip_address' in metadata:
                        print(f"      IP: {metadata['ip_address']}")
                    if 'original_url' in metadata:
                        print(f"      Original URL: {metadata['original_url']}")
                except:
                    pass
            print()
        
        if len(events) > 10:
            print(f"   ... and {len(events) - 10} more events")
        
        # Show note if applicable
        note = events_data.get('note')
        if note:
            print(f"ℹ️  {note}")
    else:
        print("📝 No events found for this campaign")
        print()
        print("💡 This could mean:")
        print("   - The campaign is very recent and emails haven't been opened yet")
        print("   - Email clients are blocking tracking pixels")
        print("   - The campaign ID doesn't exist")
        print("   - There was an issue with the tracking system")
    
    print("\n🧪 To generate events:")
    print("   1. Open your email → creates 'open' event")
    print("   2. Click any links → creates 'click' events")
    print("   3. Run this script again to see new events")
    print(f"\n💡 Quick test: python3 check_events_api.py {campaign_id}")

if __name__ == "__main__":
    main()