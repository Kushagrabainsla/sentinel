#!/usr/bin/env python3
"""
Fetch all tracking events for a campaign using the Sentinel Events API.
This script uses HTTP requests to the tracking API, not direct AWS CLI.
"""

import requests
import json
import sys
from datetime import datetime

def fetch_campaign_events(campaign_id, base_url="https://api.thesentinel.site"):
    """
    Fetch all events for a campaign using the Events API
    
    Args:
        campaign_id: The campaign ID to fetch events for
        base_url: Base URL for the Sentinel API
    
    Returns:
        dict: API response with events data
    """
    
    # Construct the events API endpoint
    events_url = f"{base_url}/events/{campaign_id}"
    
    print(f"📊 Fetching events for campaign: {campaign_id}")
    print(f"🔗 API Endpoint: {events_url}")
    print("-" * 60)
    
    try:
        # Make the API request
        response = requests.get(events_url, timeout=30)
        
        # Check if request was successful
        if response.status_code == 200:
            events_data = response.json()
            return events_data
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Could not connect to the API")
        print("   Make sure the API is deployed and accessible")
        return None
    except requests.exceptions.Timeout:
        print("❌ Timeout Error: API request took too long")
        return None
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return None

def format_timestamp(timestamp):
    """Convert Unix timestamp to readable format"""
    try:
        return datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return str(timestamp)

def display_events_summary(events_data):
    """Display a formatted summary of campaign events"""
    
    if not events_data:
        print("❌ No events data to display")
        return
    
    campaign_id = events_data.get('campaign_id', 'Unknown')
    total_events = events_data.get('total_events', 0)
    event_summary = events_data.get('event_summary', {})
    events = events_data.get('events', [])
    
    print(f"📈 Campaign Events Summary")
    print(f"Campaign ID: {campaign_id}")
    print(f"Total Events: {total_events}")
    print()
    
    # Display event type breakdown
    print("📊 Event Breakdown:")
    for event_type, count in event_summary.items():
        print(f"  {event_type.capitalize()}: {count}")
    print()
    
    # Display recent events
    if events:
        print(f"📋 Recent Events (showing {len(events)}):")
        print("-" * 80)
        print(f"{'Time':<20} {'Type':<10} {'Recipient':<25} {'Details'}")
        print("-" * 80)
        
        for event in events[:10]:  # Show first 10 events
            timestamp = format_timestamp(event.get('created_at', ''))
            event_type = event.get('type', 'unknown')
            recipient_id = event.get('recipient_id', 'unknown')
            email = event.get('email', 'unknown')
            
            # Parse metadata for additional details
            raw_metadata = event.get('raw', '{}')
            try:
                metadata = json.loads(raw_metadata)
                details = ""
                if event_type == 'click':
                    details = f"Link: {metadata.get('link_id', 'unknown')}"
                elif event_type == 'open':
                    details = f"Method: {metadata.get('method', 'unknown')}"
                else:
                    details = f"Email: {email[:20]}..."
            except:
                details = f"Email: {email[:20]}..."
            
            print(f"{timestamp:<20} {event_type:<10} {recipient_id:<25} {details}")
    else:
        print("📭 No recent events found")
    
    # Check if there are more events
    note = events_data.get('note')
    if note:
        print(f"\nℹ️  {note}")

def main():
    print("📊 Sentinel Campaign Events Fetcher")
    print("=" * 50)
    
    # Get campaign ID from command line argument or prompt
    if len(sys.argv) > 1:
        campaign_id = sys.argv[1]
    else:
        campaign_id = input("Enter Campaign ID: ").strip()
    
    if not campaign_id:
        print("❌ Campaign ID is required")
        print("Usage: python fetch_campaign_events.py <campaign_id>")
        return
    
    # Optional: Custom API base URL
    base_url = "https://api.thesentinel.site"
    if len(sys.argv) > 2:
        base_url = sys.argv[2]
    
    # Fetch and display events
    events_data = fetch_campaign_events(campaign_id, base_url)
    
    if events_data:
        display_events_summary(events_data)
        
        # Option to save raw data
        save_raw = input("\n💾 Save raw JSON data to file? (y/N): ").strip().lower()
        if save_raw in ['y', 'yes']:
            filename = f"campaign_{campaign_id}_events.json"
            with open(filename, 'w') as f:
                json.dump(events_data, f, indent=2)
            print(f"✅ Raw data saved to {filename}")
    else:
        print("❌ Could not fetch campaign events")
        print()
        print("🔧 Troubleshooting:")
        print("1. Check if the campaign ID is correct")
        print("2. Verify the API is deployed and running")
        print("3. Ensure you have internet connectivity")
        print("4. Try with a different campaign ID")

if __name__ == "__main__":
    main()