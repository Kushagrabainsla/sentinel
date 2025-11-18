import os
import time
import uuid
import json
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

def record_event(campaign_id, email, etype, raw):
    table_name = os.environ.get("DYNAMODB_EVENTS_TABLE")
    if not table_name:
        raise RuntimeError("DYNAMODB_EVENTS_TABLE env var not set")
    table = _get_dynamo().Table(table_name)
    item = {
        'id': str(uuid.uuid4()),
        'campaign_id': str(campaign_id),
        'email': email,
        'type': etype,
        'created_at': int(time.time()),
        'raw': json.dumps(raw)
    }
    table.put_item(Item=item)

def update_recipient_by_campaign_and_email(campaign_id, email, status):
    """Update recipient by campaign_id + email using a GSI on (campaign_id, email)"""
    recipients_table = os.environ.get("DYNAMODB_RECIPIENTS_TABLE")
    if not recipients_table:
        raise RuntimeError("DYNAMODB_RECIPIENTS_TABLE env var not set")
    table = _get_dynamo().Table(recipients_table)
    # Query GSI 'campaign_email_index' to find the recipient_id
    resp = table.query(
        IndexName='campaign_email_index',
        KeyConditionExpression=boto3.dynamodb.conditions.Key('campaign_id').eq(str(campaign_id)) & boto3.dynamodb.conditions.Key('email').eq(email)
    )
    items = resp.get('Items', [])
    for it in items:
        table.update_item(
            Key={'campaign_id': it['campaign_id'], 'recipient_id': it['recipient_id']},
            UpdateExpression='SET #s = :s, last_event_at = :t',
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': status, ':t': int(time.time())}
        )
