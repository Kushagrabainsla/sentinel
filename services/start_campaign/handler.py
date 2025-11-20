import json
import os
import math
import boto3
from common_db import fetch_all_active_contacts, write_recipients_batch, update_campaign_state, fetch_campaign_details, CampaignState

SQS_URL = os.environ.get("SEND_QUEUE_URL")  # set by Terraform (queues module)

sqs = boto3.client("sqs")

def _chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def lambda_handler(event, _context):
    """
    Event can be:
      - direct invoke: {"campaign_id": 123}
      - API Gateway payload: {"body": "{\"campaign_id\":123}"}
      - EventBridge Scheduler input: {"campaign_id":123}
    """
    payload = event
    if "body" in event and isinstance(event["body"], str):
        try:
            payload = json.loads(event["body"])
        except Exception:
            payload = {}

    campaign_id = payload.get("campaign_id")
    if not campaign_id:
        return {"statusCode": 400, "body": json.dumps({"error": "campaign_id required"})}

    # Fetch campaign details including direct email content
    campaign = fetch_campaign_details(campaign_id)
    if not campaign:
        return {"statusCode": 404, "body": json.dumps({"error": "Campaign not found"})}

    # Materialize recipients (example: all active contacts).
    # In real life, resolve segment_id from campaigns table then select accordingly.
    contacts = fetch_all_active_contacts()
    if not contacts:
        update_campaign_state(campaign_id, CampaignState.DONE)
        return {"statusCode": 200, "body": json.dumps({"message": "no recipients"})}

    # Write recipients table for tracking (idempotent upsert)
    for chunk in _chunks(contacts, 500):
        recipients = [{'id': c['id'], 'email': c.get('email')} for c in chunk]
        write_recipients_batch(campaign_id, recipients)
    
    # Fan out to SQS in batches of up to 10 messages
    for batch in _chunks(contacts, 10):
        entries = []
        for c in batch:
            message_body = {
                "campaign_id": campaign_id,
                "recipient_id": c["id"],
                "email": c["email"],
                "template_data": {
                    "subject": campaign.get("email_subject", campaign.get("subject", "")),
                    "html_body": campaign.get("email_body", campaign.get("html_body", "")),
                    "from_email": campaign.get("from_email", "noreply@thesentinel.site"),
                    "from_name": campaign.get("from_name", "Sentinel")
                }
            }
            
            # Inline tracking is used by default
            
            entries.append({
                "Id": str(c["id"]),
                "MessageBody": json.dumps(message_body),
            })
        sqs.send_message_batch(QueueUrl=SQS_URL, Entries=entries)

    # Mark campaign as "sending"
    update_campaign_state(campaign_id, CampaignState.SENDING)

    return {"statusCode": 200, "body": json.dumps({"campaign_id": campaign_id, "enqueued": len(contacts)})}
