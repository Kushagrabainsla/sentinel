import os
import time
import uuid
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

def fetch_all_active_contacts():
    """Return list of active contacts as dicts: {id, email}"""
    table_name = os.environ.get("DYNAMODB_CONTACTS_TABLE")
    if not table_name:
        raise RuntimeError("DYNAMODB_CONTACTS_TABLE env var not set")
    table = _get_dynamo().Table(table_name)
    # Scan for active contacts (small datasets); for large datasets use segments/GSI
    resp = table.scan(FilterExpression=boto3.dynamodb.conditions.Attr('status').eq('active'))
    items = resp.get('Items', [])
    # Normalize to expected shape
    return [{'id': it['id'], 'email': it.get('email')} for it in items]

def write_recipients_batch(campaign_id, recipients):
    """Write a batch of recipient items to recipients table. recipients is list of dicts with id and email."""
    table_name = os.environ.get("DYNAMODB_RECIPIENTS_TABLE")
    if not table_name:
        raise RuntimeError("DYNAMODB_RECIPIENTS_TABLE env var not set")
    table = _get_dynamo().Table(table_name)
    with table.batch_writer() as batch:
        for r in recipients:
            item = {
                'campaign_id': str(campaign_id),
                'recipient_id': str(r['id']),
                'email': r.get('email'),
                'status': 'pending',
                'created_at': int(time.time()),
            }
            batch.put_item(Item=item)

def update_campaign_state(campaign_id, state):
    table_name = os.environ.get("DYNAMODB_CAMPAIGNS_TABLE")
    if not table_name:
        raise RuntimeError("DYNAMODB_CAMPAIGNS_TABLE env var not set")
    table = _get_dynamo().Table(table_name)
    table.update_item(
        Key={'id': str(campaign_id)},
        UpdateExpression='SET #s = :s',
        ExpressionAttributeNames={'#s': 'state'},
        ExpressionAttributeValues={':s': state}
    )

def fetch_campaign_details(campaign_id):
    """Fetch campaign details including direct email content"""
    table_name = os.environ.get("DYNAMODB_CAMPAIGNS_TABLE")
    if not table_name:
        raise RuntimeError("DYNAMODB_CAMPAIGNS_TABLE env var not set")
    table = _get_dynamo().Table(table_name)
    
    try:
        response = table.get_item(Key={'id': str(campaign_id)})
        return response.get('Item')
    except ClientError as e:
        print(f"Error fetching campaign {campaign_id}: {e}")
        return None
