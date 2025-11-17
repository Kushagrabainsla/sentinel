import json
import os

import boto3

rds = boto3.client("rds-data")

DB_ARN = os.environ["DB_ARN"]
SECRET_ARN = os.environ["SECRET_ARN"]


def _sql(sql: str, params: list | None = None):
    return rds.execute_statement(
        resourceArn=DB_ARN,
        secretArn=SECRET_ARN,
        database="sentinel",
        sql=sql,
        parameters=params or [],
    )


def lambda_handler(event, context):
    for rec in event.get("Records", []):
        msg = json.loads(rec["Sns"]["Message"])
        event_type = msg.get("eventType", "unknown")
        mail = msg.get("mail", {})
        ts = mail.get("timestamp", "")
        provider_msg_id = mail.get("messageId", "")

        _sql(
            """
            INSERT INTO events (type, ts, meta, provider_msg_id)
            VALUES (:t, :ts, :m, :pid)
            ON CONFLICT (provider_msg_id) DO NOTHING;
            """,
            [
                {"name": "t", "value": {"stringValue": event_type}},
                {"name": "ts", "value": {"stringValue": ts}},
                {"name": "m", "value": {"stringValue": json.dumps(msg)}},
                {"name": "pid", "value": {"stringValue": provider_msg_id}},
            ],
        )
