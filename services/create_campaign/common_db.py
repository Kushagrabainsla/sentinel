import os
import uuid
import time
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

def create_campaign(name, template_id, segment_id, schedule_at=None, subject=None, html_body=None, text_body=None, from_email=None, from_name=None):
    """Create a campaign item and return its id (string UUID)."""
    table_name = os.environ.get("DYNAMODB_CAMPAIGNS_TABLE")
    if not table_name:
        raise RuntimeError("DYNAMODB_CAMPAIGNS_TABLE env var not set")

    table = _get_dynamo().Table(table_name)
    campaign_id = str(uuid.uuid4())
    item = {
        "id": campaign_id,
        "name": name,
        "template_id": template_id,
        "segment_id": segment_id,
        "schedule_at": schedule_at,
        "state": "scheduled",
        "created_at": int(time.time()),
    }
    
    # Add direct email content if provided
    if subject:
        item["subject"] = subject
    if html_body:
        item["html_body"] = html_body
    if text_body:
        item["text_body"] = text_body
    if from_email:
        item["from_email"] = from_email
    if from_name:
        item["from_name"] = from_name
    
    try:
        table.put_item(Item=item)
    except ClientError:
        raise
    return campaign_id

def execute(sql, params=None):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params or [])
        conn.commit()