import os
import uuid
import time
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

# Campaign Type Enums
class CampaignType:
    IMMEDIATE = "I"  # Immediate execution
    SCHEDULED = "S"  # Scheduled execution

# Campaign State Enums
class CampaignState:
    SCHEDULED = "SC"  # Scheduled for future execution
    PENDING = "P"     # Pending immediate execution
    SENDING = "SE"    # Currently sending
    DONE = "D"        # Completed
    FAILED = "F"      # Failed

# Campaign Status Enums
class CampaignStatus:
    ACTIVE = "A"      # Active campaign
    INACTIVE = "I"    # Inactive campaign

_dynamo = None

def _get_dynamo():
    global _dynamo
    if _dynamo is None:
        session = boto3.session.Session()
        region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
        _dynamo = session.resource("dynamodb", region_name=region)
    return _dynamo

def create_campaign(name, segment_id, campaign_type, schedule_at=None, subject=None, html_body=None, from_email=None, from_name=None):
    """Create a campaign item and return its id (string UUID)."""
    table_name = os.environ.get("DYNAMODB_CAMPAIGNS_TABLE")
    if not table_name:
        raise RuntimeError("DYNAMODB_CAMPAIGNS_TABLE env var not set")

    table = _get_dynamo().Table(table_name)
    campaign_id = str(uuid.uuid4())
    current_timestamp = int(time.time())
    
    # Validate campaign_type and schedule_at requirements
    if campaign_type == CampaignType.SCHEDULED:
        if not schedule_at:
            raise ValueError("schedule_at is required for scheduled campaigns")
    elif campaign_type == CampaignType.IMMEDIATE:
        if schedule_at:
            raise ValueError("schedule_at should not be provided for immediate campaigns")
    else:
        raise ValueError(f"Invalid campaign_type: {campaign_type}. Must be '{CampaignType.IMMEDIATE}' or '{CampaignType.SCHEDULED}'")
    
    # schedule_at is provided as epoch timestamp directly
    
    item = {
        "id": campaign_id,
        "name": name,
        "created_at": current_timestamp,
        "updated_at": current_timestamp,
        "type": campaign_type,
        "email_subject": subject or "",
        "email_body": html_body or "",
        "from_email": from_email or "noreply@thesentinel.site",
        "from_name": from_name or "Sentinel",
        "segment_id": segment_id,
        "schedule_at": schedule_at,
        "state": CampaignState.SCHEDULED if campaign_type == CampaignType.SCHEDULED else CampaignState.PENDING,
        "status": CampaignStatus.ACTIVE,
        "tags": [],  # For categorization and filtering
        "metadata": {}  # For additional custom fields
    }
    
    try:
        table.put_item(Item=item)
    except ClientError:
        raise
    return campaign_id

def update_campaign_status(campaign_id, status):
    """Update campaign status using enum values"""
    table_name = os.environ.get("DYNAMODB_CAMPAIGNS_TABLE")
    if not table_name:
        raise RuntimeError("DYNAMODB_CAMPAIGNS_TABLE env var not set")

    table = _get_dynamo().Table(table_name)
    
    try:
        table.update_item(
            Key={'id': str(campaign_id)},
            UpdateExpression="SET #status = :status, updated_at = :updated_at",
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': status,
                ':updated_at': int(time.time())
            }
        )
    except ClientError as e:
        print(f"Error updating campaign status: {e}")

def update_campaign_state(campaign_id, state):
    """Update campaign execution state using enum values"""
    table_name = os.environ.get("DYNAMODB_CAMPAIGNS_TABLE")
    if not table_name:
        raise RuntimeError("DYNAMODB_CAMPAIGNS_TABLE env var not set")

    table = _get_dynamo().Table(table_name)
    
    try:
        table.update_item(
            Key={'id': str(campaign_id)},
            UpdateExpression="SET #state = :state, updated_at = :updated_at",
            ExpressionAttributeNames={'#state': 'state'},
            ExpressionAttributeValues={
                ':state': state,
                ':updated_at': int(time.time())
            }
        )
    except ClientError as e:
        print(f"Error updating campaign state: {e}")

def update_campaign_metadata(campaign_id, **metadata_updates):
    """Update campaign metadata fields like tags, custom metadata"""
    table_name = os.environ.get("DYNAMODB_CAMPAIGNS_TABLE")
    if not table_name:
        raise RuntimeError("DYNAMODB_CAMPAIGNS_TABLE env var not set")

    table = _get_dynamo().Table(table_name)
    
    # Build update expression dynamically
    update_expression = "SET updated_at = :updated_at"
    expression_values = {":updated_at": int(time.time())}
    
    for key, value in metadata_updates.items():
        if key in ["tags", "metadata"]:
            update_expression += f", {key} = :{key}"
            expression_values[f":{key}"] = value
    
    try:
        table.update_item(
            Key={'id': str(campaign_id)},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
    except ClientError as e:
        print(f"Error updating campaign metadata: {e}")

