import json
from common_db import execute

def lambda_handler(event, _context):
    """
    Subscribed to SNS topic that receives SES notifications.
    Handles 'Bounce', 'Complaint', 'Delivery', 'Open', 'Click' (depending on SES setup).
    """
    for rec in event.get("Records", []):
        if rec.get("EventSource") == "aws:sns":
            msg = json.loads(rec["Sns"]["Message"])
        else:
            msg = rec  # fallback

        etype = msg.get("notificationType") or msg.get("eventType") or "unknown"
        mail = msg.get("mail", {})
        destination = (mail.get("destination") or ["unknown@example.com"])[0]
        headers = {h["name"].lower(): h["value"] for h in mail.get("headers", []) if "name" in h and "value" in h}
        campaign_id = None
        try:
            campaign_id = int(headers.get("x-campaign-id") or headers.get("campaign-id") or 0)
        except Exception:
            campaign_id = 0

        # Record event to your events table (ensure table exists in migrations)
        execute(
            "INSERT INTO events (campaign_id, email, type, created_at, raw) VALUES (%s, %s, %s, now(), %s::jsonb)",
            [campaign_id, destination, etype.lower(), json.dumps(msg)]
        )

        # Update recipient status on bounces/complaints
        if campaign_id and etype in ("Bounce", "Complaint"):
            status = "bounced" if etype == "Bounce" else "complained"
            execute(
                "UPDATE recipients SET status=%s, last_event_at=now() WHERE campaign_id=%s AND email=%s",
                [status, campaign_id, destination]
            )

    return {"statusCode": 200, "body": json.dumps({"ok": True})}
