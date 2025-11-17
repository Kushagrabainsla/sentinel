import json
import os
from datetime import datetime, timezone

import boto3

rds = boto3.client("rds-data")
eventbridge = boto3.client("scheduler")
sqs = boto3.client("sqs")

DB_ARN = os.environ["DB_ARN"]
SECRET_ARN = os.environ["SECRET_ARN"]
START_QUEUE_URL = os.environ["START_CAMPAIGN_QUEUE_URL"]
START_CAMPAIGN_LAMBDA_ARN = os.environ.get("START_CAMPAIGN_LAMBDA_ARN")
EVENTBRIDGE_ROLE_ARN = os.environ.get("EVENTBRIDGE_ROLE_ARN", "")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sql(sql: str, params: list | None = None):
    return rds.execute_statement(
        resourceArn=DB_ARN,
        secretArn=SECRET_ARN,
        database="sentinel",
        sql=sql,
        parameters=params or [],
    )


def _resp(code: int, payload: dict) -> dict:
    return {"statusCode": code, "body": json.dumps(payload)}


def lambda_handler(event, context):
    body = json.loads(event.get("body") or "{}")

    name = body.get("name")
    template_id = body.get("template_id")
    segment_id = body.get("segment_id")
    schedule_at = body.get("schedule_at")  # ISO8601 string or None

    if not name or not template_id or not segment_id:
        return _resp(400, {"error": "name, template_id, segment_id are required"})

    created_at = _now_iso()
    state = "scheduled" if schedule_at else "sending"

    result = _sql(
        """
        INSERT INTO campaigns (name, template_id, segment_id, schedule_at, state, created_at)
        VALUES (:n, :t, :s, :at, :st, :ca)
        RETURNING id;
        """,
        [
            {"name": "n", "value": {"stringValue": name}},
            {"name": "t", "value": {"stringValue": template_id}},
            {"name": "s", "value": {"stringValue": segment_id}},
            {"name": "at", "value": {"stringValue": schedule_at or created_at}},
            {"name": "st", "value": {"stringValue": state}},
            {"name": "ca", "value": {"stringValue": created_at}},
        ],
    )

    campaign_id = result["records"][0][0]["longValue"]

    if schedule_at:
        # Create an EventBridge Scheduler schedule to start later
        eventbridge.create_schedule(
            Name=f"start_campaign_{campaign_id}",
            ScheduleExpression=f"at({schedule_at})",
            FlexibleTimeWindow={"Mode": "OFF"},
            Target={
                "Arn": START_CAMPAIGN_LAMBDA_ARN,
                "RoleArn": EVENTBRIDGE_ROLE_ARN,
                "Input": json.dumps({"campaign_id": campaign_id}),
            },
        )
        return _resp(
            201,
            {"campaign_id": campaign_id, "state": "scheduled", "schedule_at": schedule_at},
        )

    # Start immediately (enqueue signal for StartCampaign)
    sqs.send_message(
        QueueUrl=START_QUEUE_URL,
        MessageBody=json.dumps({"campaign_id": campaign_id}),
    )
    return _resp(201, {"campaign_id": campaign_id, "state": "sending"})
