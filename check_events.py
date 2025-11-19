#!/usr/bin/env python3
"""
Simple script to check tracking events using AWS CLI.
Usage: python3 check_events.py [campaign_id]
"""
import json
import subprocess
import sys
from datetime import datetime, timezone

def run_aws_command(command):
    """Run AWS CLI command and return JSON result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return json.loads(result.stdout) if result.stdout.strip() else None
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"❌ AWS command failed: {e}")
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

def convert_dynamodb_item(item):
    """Convert DynamoDB item format to regular Python dict"""
    converted = {}
    for key, value in item.items():
        if isinstance(value, dict):
            if 'S' in value:
                converted[key] = value['S']
            elif 'N' in value:
                try:
                    converted[key] = int(value['N'])
                except ValueError:
                    converted[key] = float(value['N'])
        else:
            converted[key] = value
    return converted

def main():
    if len(sys.argv) > 1:
        campaign_id = sys.argv[1]
    else:
        print("💡 Usage: python3 check_events.py <campaign_id>")
        print("\nGet your campaign ID from: python3 send_campaign.py immediate")
        campaign_id = input("Enter campaign ID: ").strip()
        if not campaign_id:
            print("❌ Campaign ID required")
            return
    
    print(f"🔍 Checking events for campaign: {campaign_id}\n")
    
    # Check events in DynamoDB
    command = f'aws dynamodb scan --table-name sentinel-events --filter-expression "campaign_id = :cid" --expression-attribute-values \'{{":cid":{{"S":"{campaign_id}"}}}}\' --region us-east-1'
    
    print("📊 Scanning DynamoDB events table...")
    result = run_aws_command(command)
    
    if not result or not result.get('Items'):
        print("📝 No tracking events found for this campaign")
        print("\n💡 To generate events:")
        print("   1. Open the email you received")
        print("   2. Click any links in the email")
        print("   3. Run this script again")
        return
    
    # Convert and sort events
    events = [convert_dynamodb_item(item) for item in result['Items']]
    events.sort(key=lambda x: x.get('created_at', 0), reverse=True)
    
    print(f"✅ Found {len(events)} events!")
    
    # Show event summary
    event_types = {}
    for event in events:
        event_type = event.get('type', 'unknown')
        event_types[event_type] = event_types.get(event_type, 0) + 1
    
    print("\n📊 Event Summary:")
    for event_type, count in event_types.items():
        print(f"   - {event_type}: {count}")
    
    print(f"\n📝 Recent Events:")
    for i, event in enumerate(events[:5], 1):
        event_type = event.get('type', 'unknown')
        email = event.get('email', 'unknown')
        timestamp = format_timestamp(event.get('created_at'))
        
        print(f"\n   {i}. {event_type.upper()} Event")
        print(f"      Email: {email}")
        print(f"      Time: {timestamp}")
        
        # Show metadata if available
        raw_metadata = event.get('raw')
        if raw_metadata:
            try:
                metadata = json.loads(raw_metadata)
                if 'ip_address' in metadata:
                    print(f"      IP: {metadata['ip_address']}")
                if 'original_url' in metadata:
                    print(f"      URL: {metadata['original_url']}")
            except:
                pass
    
    if len(events) > 5:
        print(f"\n   ... and {len(events) - 5} more events")

if __name__ == "__main__":
    main()