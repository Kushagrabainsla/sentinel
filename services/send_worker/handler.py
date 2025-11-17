import json
import os

import boto3
from botocore.exceptions import ClientError

ses = boto3.client("sesv2")

SES_FROM_ADDRESS = os.environ["SES_FROM_ADDRESS"]
SES_TEMPLATE_ARN = os.environ["SES_TEMPLATE_ARN"]


def _destinations(recipients: list[dict]) -> list[dict]:
    return [
        {
            "Destination": {"ToAddresses": [r["email"]]},
            "ReplacementTemplateData": json.dumps({"email": r["email"]}),
        }
        for r in recipients
    ]


def lambda_handler(event, context):
    for record in event.get("Records", []):
        message = json.loads(record["body"])
        recipients = message.get("recipients", [])
        if not recipients:
            continue

        try:
            ses.send_bulk_templated_email(
                Source=SES_FROM_ADDRESS,
                Template=SES_TEMPLATE_ARN,
                DefaultTemplateData=json.dumps({"default": True}),
                Destinations=_destinations(recipients),
            )
        except ClientError as exc:
            # Let SQS redrive policy & retries handle transient errors
            print(f"SES error for batch: {exc}")
