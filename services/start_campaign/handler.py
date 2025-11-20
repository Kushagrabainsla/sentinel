import json
import os
import math
import boto3
from common_db import (fetch_all_active_contacts, record_segment_campaign, update_campaign_state, 
                       fetch_campaign_details, CampaignState, CampaignDeliveryType, get_campaign_recipients)

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

    # Materialize recipients based on campaign delivery type
    try:
        contacts = get_campaign_recipients(campaign)
    except ValueError as e:
        update_campaign_state(campaign_id, CampaignState.FAILED)
        return {"statusCode": 400, "body": json.dumps({"error": str(e)})}
    
    if not contacts:
        update_campaign_state(campaign_id, CampaignState.DONE)
        delivery_type = campaign.get('delivery_type', CampaignDeliveryType.SEGMENT)
        message = f"no recipients found for {'individual' if delivery_type == CampaignDeliveryType.INDIVIDUAL else 'segment'} campaign"
        return {"statusCode": 200, "body": json.dumps({"message": message})}

    # Record campaign execution in segments table for tracking
    delivery_type = campaign.get('delivery_type', CampaignDeliveryType.SEGMENT)
    if delivery_type == CampaignDeliveryType.SEGMENT:
        segment_id = campaign.get('segment_id')
        recipient_emails = [c.get('email') for c in contacts if c.get('email')]
        record_segment_campaign(campaign_id, segment_id, recipient_emails)
    
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

    delivery_type = campaign.get('delivery_type', CampaignDeliveryType.SEGMENT)
    response_data = {
        "campaign_id": campaign_id, 
        "enqueued": len(contacts),
        "delivery_type": delivery_type,
        "recipient_count": len(contacts)
    }
    
    if delivery_type == CampaignDeliveryType.INDIVIDUAL:
        response_data["recipient_email"] = campaign.get('recipient_email')
    else:
        response_data["segment_id"] = campaign.get('segment_id')
    
    return {"statusCode": 200, "body": json.dumps(response_data)}
