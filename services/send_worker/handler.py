import json
import os
import boto3
from common_db import update_recipient_status

ses = boto3.client("ses")
FROM = os.environ.get("SES_FROM_ADDRESS")       # set in Terraform
TEMPLATE = os.environ.get("SES_TEMPLATE_ARN")   # set in Terraform (name is fine)

def lambda_handler(event, _context):
    """
    Triggered by SQS event. Each record has body:
    {"campaign_id":123, "recipient_id":456, "email":"user@example.com"}
    """
    for rec in event.get("Records", []):
        body = json.loads(rec["body"])
        campaign_id = body["campaign_id"]
        recipient_id = body["recipient_id"]
        email = body["email"]

        try:
            # Send email via SES (TemplateName should exist)
            ses.send_templated_email(
                Source=FROM,
                Destination={"ToAddresses": [email]},
                Template=TEMPLATE,
                TemplateData=json.dumps({"name": email.split("@")[0]}),
            )
            status = "sent"
        except Exception:
            status = "failed"

        # Update recipient status
        update_recipient_status(campaign_id, recipient_id, status)

    return {"statusCode": 200, "body": json.dumps({"processed": len(event.get('Records', []))})}
