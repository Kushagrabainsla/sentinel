import json
import os
import math
import boto3
from common_db import fetch_all, execute

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

    # Materialize recipients (example: all active contacts).
    # In real life, resolve segment_id from campaigns table then select accordingly.
    contacts = fetch_all("SELECT id, email FROM contacts WHERE status = 'active'")
    if not contacts:
        execute("UPDATE campaigns SET state = 'done' WHERE id = %s", [campaign_id])
        return {"statusCode": 200, "body": json.dumps({"message": "no recipients"})}

    # Write recipients table for tracking (idempotent upsert)
    # NOTE: Use ON CONFLICT if you have a unique key (campaign_id, recipient_id)
    for chunk in _chunks(contacts, 500):
        values = [(campaign_id, c["id"], c["email"]) for c in chunk]
        # Efficient multi-row insert
        params = []
        ph = []
        for (cid, rid, email) in values:
            ph.append("(%s, %s, %s, 'pending', now())")
            params.extend([cid, rid, email])
        execute(
            f"INSERT INTO recipients (campaign_id, recipient_id, email, status, created_at) "
            f"VALUES {', '.join(ph)} "
            f"ON CONFLICT (campaign_id, recipient_id) DO NOTHING",
            params
        )

    # Fan out to SQS in batches of up to 10 messages
    for batch in _chunks(contacts, 10):
        entries = []
        for c in batch:
            entries.append({
                "Id": str(c["id"]),
                "MessageBody": json.dumps({
                    "campaign_id": campaign_id,
                    "recipient_id": c["id"],
                    "email": c["email"],
                }),
            })
        sqs.send_message_batch(QueueUrl=SQS_URL, Entries=entries)

    # Mark campaign as "sending"
    execute("UPDATE campaigns SET state = 'sending' WHERE id = %s", [campaign_id])

    return {"statusCode": 200, "body": json.dumps({"campaign_id": campaign_id, "enqueued": len(contacts)})}
