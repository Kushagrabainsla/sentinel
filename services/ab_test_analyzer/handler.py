import json
import os
import time
import boto3
import hashlib
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
from common import CampaignState, CampaignStatus, EventType, CampaignDeliveryType, SegmentStatus

# Database utilities
_dynamo = None

def _get_dynamo():
    global _dynamo
    if _dynamo is None:
        session = boto3.session.Session()
        region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
        _dynamo = session.resource("dynamodb", region_name=region)
    return _dynamo

def get_table(env_var):
    table_name = os.environ.get(env_var)
    if not table_name:
        raise RuntimeError(f"{env_var} env var not set")
    return _get_dynamo().Table(table_name)

def fetch_campaign(campaign_id):
    table = get_table("DYNAMODB_CAMPAIGNS_TABLE")
    resp = table.get_item(Key={'id': str(campaign_id)})
    return resp.get('Item')

def update_campaign_winner(campaign_id, winner_id):
    table = get_table("DYNAMODB_CAMPAIGNS_TABLE")
    table.update_item(
        Key={'id': str(campaign_id)},
        UpdateExpression='SET ab_test_config.winner_id = :w, updated_at = :t',
        ExpressionAttributeValues={
            ':w': winner_id,
            ':t': int(time.time())
        }
    )

def update_campaign_state(campaign_id, state):
    table = get_table("DYNAMODB_CAMPAIGNS_TABLE")
    table.update_item(
        Key={'id': str(campaign_id)},
        UpdateExpression='SET #s = :s, updated_at = :t',
        ExpressionAttributeNames={'#s': 'state'},
        ExpressionAttributeValues={
            ':s': state,
            ':t': int(time.time())
        }
    )

def get_campaign_events(campaign_id):
    table = get_table("DYNAMODB_EVENTS_TABLE")
    # Query events for this campaign
    # We need to scan or query. Ideally query by campaign_id index.
    # Assuming 'campaign_index' exists on campaign_id
    resp = table.query(
        IndexName='campaign_index',
        KeyConditionExpression=Key('campaign_id').eq(str(campaign_id))
    )
    return resp.get('Items', [])

def fetch_segment_contacts(segment_id):
    """Return list of contacts for a specific segment as dicts: {id, email}"""
    if not segment_id: return []
    
    segments_table = get_table("DYNAMODB_SEGMENTS_TABLE")
    
    # Handle built-in segments (simplified for now, assuming custom segments mostly)
    if segment_id in ["all_active", "all_contacts"]:
        # Fallback to scan if needed, but for A/B test we usually use custom segments
        # For brevity, implementing scan
        resp = segments_table.scan()
        segments = resp.get('Items', [])
        all_emails = set()
        for seg in segments:
            if segment_id == "all_active" and seg.get('status') != SegmentStatus.ACTIVE.value: continue
            all_emails.update(seg.get('emails', []))
        
        contacts = []
        for email in all_emails:
            email_id = hashlib.md5(email.encode()).hexdigest()[:12]
            contacts.append({'id': email_id, 'email': email})
        return contacts

    resp = segments_table.get_item(Key={'id': segment_id})
    if 'Item' not in resp: return []
    
    segment = resp['Item']
    emails = segment.get('emails', [])
    contacts = []
    for email in emails:
        email_id = hashlib.md5(f"{segment_id}:{email}".encode()).hexdigest()[:12]
        contacts.append({'id': email_id, 'email': email})
    return contacts

def get_campaign_recipients(campaign):
    delivery_type = campaign.get('delivery_type', CampaignDeliveryType.SEGMENT.value)
    if delivery_type == CampaignDeliveryType.INDIVIDUAL.value:
        email = campaign.get('recipient_email')
        if not email: return []
        rid = hashlib.md5(email.encode()).hexdigest()[:8]
        return [{'id': rid, 'email': email}]
    elif delivery_type == CampaignDeliveryType.SEGMENT.value:
        return fetch_segment_contacts(campaign.get('segment_id'))
    return []

def _chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def lambda_handler(event, context):
    print(f"📊 A/B Analyzer triggered: {json.dumps(event)}")
    
    campaign_id = event.get("campaign_id")
    if not campaign_id:
        print("❌ No campaign_id provided")
        return
    
    campaign = fetch_campaign(campaign_id)
    if not campaign:
        print(f"❌ Campaign {campaign_id} not found")
        return
    
    variations = campaign.get('variations', [])
    if not variations:
        print("❌ No variations found")
        return
        
    # 1. Analyze Results
    events = get_campaign_events(campaign_id)
    
    scores = {"A": 0, "B": 0, "C": 0}
    counts = {"A": {"opens": 0, "clicks": 0}, "B": {"opens": 0, "clicks": 0}, "C": {"opens": 0, "clicks": 0}}
    
    sent_recipients = set()
    
    for e in events:
        # Track who has already been sent to
        if e.get('type') == EventType.SENT.value:
            email = e.get('email')
            if email: sent_recipients.add(email)
            
        # Analyze engagement
        raw = e.get('raw')
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except:
                raw = {}
        
        # Try to get variation_id from event metadata (raw)
        # If not present, we can't attribute it to a variation easily unless we tracked it
        # We updated tracking_api to save 'variation_id' in metadata
        var_id = raw.get('variation_id') or e.get('variation_id') # Check both top level and raw
        
        if var_id and var_id in scores:
            if e.get('type') == EventType.OPEN.value:
                scores[var_id] += 1
                counts[var_id]["opens"] += 1
            elif e.get('type') == EventType.CLICK.value:
                scores[var_id] += 2 # Clicks worth more
                counts[var_id]["clicks"] += 1
    
    print(f"📈 Analysis Results: {json.dumps(counts)}")
    
    # Determine winner
    winner_id = max(scores, key=scores.get)
    print(f"🏆 Winner is Variation {winner_id} with score {scores[winner_id]}")
    
    # Update campaign
    update_campaign_winner(campaign_id, winner_id)
    
    # 2. Send to Remainder
    all_contacts = get_campaign_recipients(campaign)
    remainder = [c for c in all_contacts if c['email'] not in sent_recipients]
    
    print(f"📦 Sending winner ({winner_id}) to {len(remainder)} remaining recipients")
    
    # Get winning content
    winning_variation = next((v for i, v in enumerate(variations) if ["A", "B", "C"][i] == winner_id), variations[0])
    
    sqs = boto3.client("sqs")
    SQS_URL = os.environ.get("SEND_QUEUE_URL")
    
    enqueued = 0
    for batch in _chunks(remainder, 10):
        entries = []
        for c in batch:
            message_body = {
                "campaign_id": campaign_id,
                "recipient_id": c["id"],
                "email": c["email"],
                "variation_id": winner_id,
                "template_data": {
                    "subject": winning_variation.get("subject"),
                    "html_body": winning_variation.get("content"),
                    "from_email": campaign.get("from_email", "noreply@thesentinel.site"),
                    "from_name": campaign.get("from_name", "Sentinel")
                }
            }
            entries.append({
                "Id": str(c["id"]),
                "MessageBody": json.dumps(message_body),
            })
        
        if entries:
            sqs.send_message_batch(QueueUrl=SQS_URL, Entries=entries)
            enqueued += len(entries)
            
    print(f"✅ Enqueued {enqueued} messages")
    
    # Mark campaign as DONE
    update_campaign_state(campaign_id, CampaignState.DONE.value)
    
    return {
        "winner": winner_id,
        "scores": scores,
        "sent_to_remainder": enqueued
    }
