import boto3
import os
import sys
from boto3.dynamodb.conditions import Key

def get_table_name(partial_name):
    client = boto3.client('dynamodb')
    # Handle pagination if many tables
    table_names = []
    paginator = client.get_paginator('list_tables')
    for page in paginator.paginate():
        table_names.extend(page['TableNames'])
        
    for name in table_names:
        if partial_name in name and 'campaigns' in name and partial_name == 'campaigns':
             return name
        if partial_name in name and 'events' in name and partial_name == 'events':
             return name
        # Fallback loose match
        if partial_name in name:
            return name
            
    return None

def fix_counts():
    print("Searching for tables...")
    # Try to find tables with 'campaigns' and 'events' in their names
    # Assuming standard naming convention like 'sentinel-campaigns-dev'
    
    client = boto3.client('dynamodb')
    table_names = []
    paginator = client.get_paginator('list_tables')
    for page in paginator.paginate():
        table_names.extend(page['TableNames'])
        
    campaigns_table_name = next((n for n in table_names if 'campaigns' in n), None)
    events_table_name = next((n for n in table_names if 'events' in n), None)
    
    if not campaigns_table_name or not events_table_name:
        print("Could not find campaigns or events table.")
        print(f"Found tables: {table_names}")
        return

    print(f"Using tables: {campaigns_table_name}, {events_table_name}")
    
    dynamodb = boto3.resource('dynamodb')
    campaigns_table = dynamodb.Table(campaigns_table_name)
    events_table = dynamodb.Table(events_table_name)
    
    # Scan campaigns
    print("Scanning campaigns...")
    response = campaigns_table.scan()
    campaigns = response['Items']
    
    print(f"Found {len(campaigns)} campaigns. Updating counts...")
    
    for campaign in campaigns:
        c_id = campaign['id']
        name = campaign.get('name', 'Unknown')
        
        # Query events
        events_resp = events_table.query(
            KeyConditionExpression=Key('campaign_id').eq(c_id)
        )
        events = events_resp['Items']
        
        # Count sent
        sent_count = sum(1 for e in events if e['type'] == 'sent')
        
        # Also check if recipient_count is already set
        current_rc = campaign.get('recipient_count')
        
        print(f"Campaign '{name}' ({c_id}): Found {sent_count} sent events (Current DB count: {current_rc})")
        
        if sent_count > 0:
            campaigns_table.update_item(
                Key={'id': c_id},
                UpdateExpression='SET recipient_count = :rc, sent_count = :sc',
                ExpressionAttributeValues={':rc': sent_count, ':sc': sent_count}
            )
            print(f"  -> Updated counts to {sent_count}")
        elif sent_count == 0 and current_rc is None:
             # If no events found, maybe it's just created? Or maybe we should set to 0?
             # Let's set to 0 to fix the display
             campaigns_table.update_item(
                Key={'id': c_id},
                UpdateExpression='SET recipient_count = :rc, sent_count = :sc',
                ExpressionAttributeValues={':rc': 0, ':sc': 0}
            )
             print(f"  -> Set counts to 0")

if __name__ == "__main__":
    fix_counts()
