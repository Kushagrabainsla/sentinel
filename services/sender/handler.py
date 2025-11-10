import base64, json, os, re, urllib.parse, uuid, time
import boto3

REGION = os.getenv("AWS_REGION", "us-east-1")
FROM_EMAIL = os.environ["FROM_EMAIL"]  # set via Terraform
EVENT_BUS  = os.getenv("EVENT_BUS", "default")

ses = boto3.client("sesv2", region_name=REGION)
events = boto3.client("events",  region_name=REGION)

# 1x1 transparent PNG
PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mO0WQ8AAgMB2bqR6kMAAAAASUVORK5CYII="
)

def _json(status: int, body: dict):
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body),
    }

def _redirect(url: str):
    return {
        "statusCode": 302,
        "headers": {"location": url},
        "body": "",
    }

def _png():
    return {
        "statusCode": 200,
        "isBase64Encoded": True,
        "headers": {"content-type": "image/png", "cache-control": "no-store"},
        "body": base64.b64encode(PIXEL_PNG).decode("utf-8"),
    }

def _emit(detail_type: str, source: str, detail: dict):
    try:
        events.put_events(
            Entries=[{
                "Source": source,
                "DetailType": detail_type,
                "Detail": json.dumps(detail),
                "EventBusName": EVENT_BUS
            }]
        )
    except Exception:
        # soft-fail eventing to not block email send/redirect
        pass

def _tracking_base(event):
    # Build "https://host/stage" for current request
    headers = event.get("headers") or {}
    host = headers.get("x-forwarded-host") or headers.get("host") or ""
    stage = (event.get("requestContext") or {}).get("stage") or ""
    scheme = "https"  # HTTP API is public HTTPS
    return f"{scheme}://{host}/{stage}".rstrip("/")

_HREF_RE = re.compile(r'href\s*=\s*"(.*?)"', re.IGNORECASE)

def _rewrite_links(html: str, base: str, msg_id: str):
    def _wrap(m):
        url = m.group(1)
        # keep mailto and already-tracked links as-is
        if url.startswith("mailto:") or url.startswith(base + "/r"):
            return f'href="{url}"'
        target = f"{base}/r?u={urllib.parse.quote_plus(url)}&m={msg_id}"
        return f'href="{target}"'
    return _HREF_RE.sub(_wrap, html)

def _inject_pixel(html: str, base: str, msg_id: str):
    pixel = f'<img src="{base}/o?m={msg_id}&t={int(time.time())}" width="1" height="1" style="display:none" alt=""/>'
    # naive inject before </body> if present; else append
    idx = html.lower().rfind("</body>")
    return (html[:idx] + pixel + html[idx:]) if idx != -1 else (html + pixel)

def _route_key(event):
    # Examples: "POST /send", "GET /r", "GET /o"
    return (event.get("requestContext") or {}).get("routeKey")

def handler(event, context):
    rk = _route_key(event)
    if rk == "POST /send":
        return send_handler(event, context)
    elif rk == "GET /r":
        return redirect_handler(event, context)
    elif rk == "GET /o":
        return open_handler(event, context)
    else:
        return _json(404, {"error": "not found", "route": rk})

def send_handler(event, context):
    # Body format: { "to": "user@example.com", "subject": "...", "html": "<p>...</p>" }
    body = event.get("body") or "{}"
    try:
        data = json.loads(body)
    except Exception:
        return _json(400, {"error": "invalid JSON body"})

    to = data.get("to")
    if not to:
        return _json(400, {"error": "missing 'to'"})

    subject = data.get("subject", "Sentinel Test")
    raw_html = data.get("html", "<p>Hello from Sentinel</p>")

    msg_id = str(uuid.uuid4())
    base = _tracking_base(event)

    html = _rewrite_links(raw_html, base, msg_id)
    html = _inject_pixel(html, base, msg_id)

    try:
        ses.send_email(
            FromEmailAddress=FROM_EMAIL,
            Destination={"ToAddresses": [to]},
            Content={
                "Simple": {
                    "Subject": {"Data": subject},
                    "Body": {"Html": {"Data": html}}
                }
            },
            EmailTags=[{"Name": "message_id", "Value": msg_id}]
        )
        _emit("EmailSent", "sentinel.sender", {"message_id": msg_id, "to": to})
        return _json(200, {"ok": True, "message_id": msg_id})
    except Exception as e:
        _emit("EmailFailed", "sentinel.sender", {"error": str(e)})
        return _json(500, {"ok": False, "error": str(e)})

def redirect_handler(event, context):
    q = event.get("queryStringParameters") or {}
    url = q.get("u")
    msg_id = q.get("m")
    if not url:
        return _json(400, {"error": "missing u"})
    try:
        dest = urllib.parse.unquote_plus(url)
    except Exception:
        return _json(400, {"error": "bad u"})
    _emit("ClickTracked", "sentinel.tracking", {
        "message_id": msg_id, "url": dest, "ts": int(time.time())
    })
    return _redirect(dest)

def open_handler(event, context):
    q = event.get("queryStringParameters") or {}
    msg_id = q.get("m")
    _emit("OpenTracked", "sentinel.tracking", {
        "message_id": msg_id, "ts": int(time.time())
    })
    return _png()
