import os
import time
import uuid
import json
import hashlib
import boto3
from botocore.exceptions import ClientError

_dynamo = None

def _get_dynamo():
    global _dynamo
    if _dynamo is None:
        session = boto3.session.Session()
        region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
        _dynamo = session.resource("dynamodb", region_name=region)
    return _dynamo

def update_email_status_in_events(campaign_id, email, status):
    """Record email send status in events table instead of recipients table"""
    table_name = os.environ.get("DYNAMODB_EVENTS_TABLE")
    if not table_name:
        print("Warning: DYNAMODB_EVENTS_TABLE env var not set")
        return
    
    table = _get_dynamo().Table(table_name)
    
    try:
        # Create a send status event
        event_record = {
            'id': str(uuid.uuid4()),
            'campaign_id': str(campaign_id),
            'recipient_id': hashlib.md5(email.encode()).hexdigest()[:8],  # Generate consistent ID from email
            'email': email,
            'type': 'send_status',
            'created_at': int(time.time()),
            'raw': json.dumps({'status': status})
        }
        
        table.put_item(Item=event_record)
    except Exception as e:
        print(f"❌ Failed to record email status: {e}")
