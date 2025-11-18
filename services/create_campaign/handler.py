import json
import os
from datetime import datetime, timezone
from common_db import create_campaign

def _parse_body(event):
    if isinstance(event, dict) and "body" in event:
        body = event["body"]
        if event.get("isBase64Encoded"):
            import base64
            body = base64.b64decode(body).decode("utf-8")
    else:
        body = event
    try:
        return json.loads(body or "{}")
    except Exception:
        return {}

def _response(code, body):
    return {
        "statusCode": code,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body),
    }

def lambda_handler(event, _context):
    data = _parse_body(event)
    name = data.get("name")
    template_id = data.get("template_id")
    segment_id = data.get("segment_id")
    schedule_at = data.get("schedule_at")  # ISO8601 or None

    if not name or not template_id or not segment_id:
        return _response(400, {"error": "name, template_id, segment_id are required"})

    # Default schedule: now (UTC)
    if not schedule_at:
        schedule_at = datetime.now(timezone.utc).isoformat()

    campaign_id = create_campaign(name, template_id, segment_id, schedule_at)

    # The web app (or create path) can immediately invoke Start Campaign via API/Lambda,
    # or EventBridge Scheduler will trigger it later, depending on schedule_at.
    return _response(201, {"campaign_id": campaign_id, "state": "scheduled"})
