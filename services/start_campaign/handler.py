import json
import math
import os

import boto3

rds = boto3.client("rds-data")
sqs = boto3.client("sqs")

DB_ARN = os.environ["DB_ARN"]
SECRET_ARN = os.environ["SECRET_ARN"]
SEND_QUEUE_URL = os.environ["SEND_QUEUE_URL"]
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "200"))


def _sql(sql: str, params: list | None = None):
    return rds.execute_statement(
        resourceArn=DB_ARN,
        secretArn=SECRET_ARN,
        database="sentinel",
        sql=sql,
        parameters=params or [],
    )


def _parse_payload(event: dict) -> dict:
    if isinstance(event, dict) and "body" in event:
        try:
            return json.loads(event.get("body") or "{}")
        except Exception:
            return {}
    return event or {}


def lambda_handler(event, context):
    payload = _parse_payload(event)
    campaign_id = payload.get("campaign_id")

    if not campaign_id:
        return {"statusCode": 400, "body": "missing campaign_id"}

    # TODO: replace with real segmentation logic
    res = _sql("SELECT id, email FROM contacts WHERE status = 'active';")
    recipients = [
        {"id": r[0]["longValue"], "email": r[1]["stringValue"]}
        for r in res.get("records", [])
    ]

    total = len(recipients)
    if total == 0:
        _sql(
            "UPDATE campaigns SET state = 'done' WHERE id = :id",
            [{"name": "id", "value": {"longValue": campaign_id}}],
        )
        return {"statusCode": 200, "body": "no recipients"}

    # Chunk and enqueue batch jobs
    for i in range(0, total, BATCH_SIZE):
        batch = recipients[i : i + BATCH_SIZE]
        msg = {
            "campaign_id": campaign_id,
            "batch_no": i // BATCH_SIZE,
            "recipients": batch,
        }
        sqs.send_message(QueueUrl=SEND_QUEUE_URL, MessageBody=json.dumps(msg))

    _sql(
        "UPDATE campaigns SET state = 'sending' WHERE id = :id",
        [{"name": "id", "value": {"longValue": campaign_id}}],
    )

    batches = math.ceil(total / BATCH_SIZE)
    return {"statusCode": 202, "body": f"queued {total} recipients in {batches} batches"}
