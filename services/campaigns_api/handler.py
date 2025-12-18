#!/usr/bin/env python3
"""
Campaigns API Service for Sentinel

Handles CRUD operations for email campaigns:
- GET /campaigns - List user's campaigns
- GET /campaigns/{id} - Get specific campaign
- POST /campaigns - Create new campaign
- PUT /campaigns/{id} - Update campaign
- DELETE /campaigns/{id} - Delete campaign
- GET /campaigns/{id}/events - Get campaign events/analytics
"""

import json
import os
import time
import uuid
import re
from decimal import Decimal
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

# Import additional enums from common
from common import (
    CampaignType, CampaignDeliveryType, CampaignState, CampaignStatus,
    EventType, EngagementLevel, _response, convert_decimals, get_user_from_context, 
    get_campaigns_table, get_events_table, get_segments_table, sanitize_html_content
)


DEFAULT_FROM_EMAIL = "no-reply@thesentinel.site"
DEFAULT_FROM_NAME = "Sentinel"

lambda_client = boto3.client('lambda', region_name=os.environ.get('AWS_REGION', 'us-east-1'))


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal objects from DynamoDB"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj % 1 == 0:
                return int(obj)
            else:
                return float(obj)
        return super(DecimalEncoder, self).default(obj)

def list_campaigns(event):
    """List user's campaigns with filtering and pagination"""
    try:
        user = event['user']  # User already authenticated in handler
        
        # Parse query parameters
        query_params = event.get('queryStringParameters') or {}
        status_filter = query_params.get('status')
        limit = int(query_params.get('limit', 50))
        limit = min(limit, 100)  # Max 100 campaigns per request
        
        campaigns_table = get_campaigns_table()
        
        # Build query parameters
        query_params = {
            'IndexName': 'owner_index',
            'KeyConditionExpression': Key('owner_id').eq(user['id']),
            'Limit': limit,
            'ScanIndexForward': False  # Most recent first
        }
        
        # Query user's campaigns using owner_id index
        response = campaigns_table.query(**query_params)
        all_campaigns = convert_decimals(response.get('Items', []))
        
        # Filter by status in Python for better reliability (handles missing attributes)
        if status_filter:
            campaigns = [c for c in all_campaigns if c.get('status') == status_filter]
        else:
            # Exclude DELETED items, include everything else
            campaigns = [c for c in all_campaigns if (c.get('status') or "").upper() not in [CampaignStatus.DELETED.value, "DELETED"]]
        
        # Sort by created_at (most recent first)
        campaigns.sort(key=lambda x: x.get('created_at', 0), reverse=True)
        
        return _response(200, {
            "campaigns": campaigns,
            "count": len(campaigns),
            "has_more": 'LastEvaluatedKey' in response
        })
        
    except ValueError as e:
        return _response(401, {"error": f"Authentication failed: {str(e)}"})
    except Exception as e:
        print(f"Error listing campaigns: {str(e)}")
        return _response(500, {"error": f"Failed to list campaigns: {str(e)}"})

def get_campaign(event):
    """Get specific campaign by ID"""
    try:
        user = event['user']  # User already authenticated in handler
        campaign_id = event['pathParameters']['id']
        
        campaigns_table = get_campaigns_table()
        
        response = campaigns_table.get_item(
            Key={'id': campaign_id}
        )
        
        if 'Item' not in response:
            return _response(404, {"error": "Campaign not found"})
        
        campaign = convert_decimals(response['Item'])
        
        # Check ownership
        if campaign.get('owner_id') != user['id']:
            return _response(403, {"error": "Access denied"})
        
        return _response(200, {"campaign": campaign})
        
    except ValueError as e:
        return _response(401, {"error": f"Authentication failed: {str(e)}"})
    except Exception as e:
        print(f"Error getting campaign: {str(e)}")
        return _response(500, {"error": f"Failed to get campaign: {str(e)}"})

def create_campaign_record(name, segment_id=None, campaign_type=None, delivery_type=None, recipient_email=None, 
                   schedule_at=None, subject=None, html_body=None, from_email=None, from_name=None, owner_id=None,
                   ab_test_config=None, variations=None):
    """Create a campaign item and return its id (string UUID)."""
    
    campaigns_table = get_campaigns_table()
    campaign_id = str(uuid.uuid4())
    current_timestamp = int(time.time())
    
    # Validate delivery_type and corresponding fields
    if not delivery_type:
        delivery_type = CampaignDeliveryType.SEGMENT.value  # Default to segment-based
    
    if delivery_type == CampaignDeliveryType.INDIVIDUAL.value:
        if not recipient_email:
            raise ValueError("recipient_email is required for individual campaigns")
        if segment_id:
            raise ValueError("segment_id should not be provided for individual campaigns")
    elif delivery_type == CampaignDeliveryType.SEGMENT.value:
        if recipient_email:
            raise ValueError("recipient_email should not be provided for segment campaigns")
        if not segment_id:
            raise ValueError("segment_id is required for segment campaigns")
    else:
        raise ValueError(f"Invalid delivery_type: {delivery_type}. Must be '{CampaignDeliveryType.INDIVIDUAL.value}' or '{CampaignDeliveryType.SEGMENT.value}'")
    
    # Validate campaign_type and schedule_at requirements
    if campaign_type == CampaignType.SCHEDULED.value:
        if not schedule_at:
            raise ValueError("schedule_at is required for scheduled campaigns")
    elif campaign_type == CampaignType.IMMEDIATE.value:
        if schedule_at:
            raise ValueError("schedule_at should not be provided for immediate campaigns")
    elif campaign_type == CampaignType.AB_TEST.value:
        if not ab_test_config:
            raise ValueError("ab_test_config is required for A/B test campaigns")
        if not variations or len(variations) != 3:
            raise ValueError("Exactly 3 variations are required for A/B test campaigns")
    else:
        raise ValueError(f"Invalid campaign_type: {campaign_type}. Must be '{CampaignType.IMMEDIATE.value}', '{CampaignType.SCHEDULED.value}' or '{CampaignType.AB_TEST.value}'")
    
    item = {
        "id": campaign_id,
        "name": name,
        "created_at": current_timestamp,
        "updated_at": current_timestamp,
        "type": campaign_type,
        "delivery_type": delivery_type,
        "email_subject": subject or "",
        "email_body": html_body or "",
        "from_email": from_email or DEFAULT_FROM_EMAIL,
        "from_name": from_name or DEFAULT_FROM_NAME,
        "segment_id": segment_id,
        "recipient_email": recipient_email,
        "schedule_at": schedule_at,
        "state": CampaignState.SCHEDULED.value if campaign_type == CampaignType.SCHEDULED.value else CampaignState.PENDING.value,
        "status": CampaignStatus.ACTIVE.value,
        "owner_id": owner_id,
        "tags": [],  # For categorization and filtering
        "metadata": {},  # For additional custom fields
        "ab_test_config": ab_test_config,
        "variations": variations
    }
    
    try:
        campaigns_table.put_item(Item=item)
    except ClientError:
        raise
    return campaign_id



def create_scheduler_rule(campaign_id, schedule_at):
    """Create EventBridge Scheduler rule to automatically start campaign"""
    scheduler = boto3.client("scheduler")
    start_lambda_arn = os.environ.get("START_CAMPAIGN_LAMBDA_ARN")
    scheduler_role_arn = os.environ.get("EVENTBRIDGE_ROLE_ARN")
    
    if not start_lambda_arn or not scheduler_role_arn:
        print(f"Missing scheduler config: lambda_arn={start_lambda_arn}, role_arn={scheduler_role_arn}")
        return False
    
    try:
        # Convert epoch timestamp to datetime
        schedule_dt = datetime.fromtimestamp(schedule_at, timezone.utc)
        
        # Only create scheduler if it's in the future
        if schedule_dt <= datetime.now(timezone.utc):
            print(f"Schedule time {schedule_at} is in the past, skipping scheduler")
            return False
        
        # Create one-time schedule
        schedule_name = f"start-campaign-{campaign_id}"
        
        scheduler.create_schedule(
            Name=schedule_name,
            Description=f"Auto-start campaign {campaign_id}",
            ScheduleExpression=f"at({schedule_dt.strftime('%Y-%m-%dT%H:%M:%S')})",
            Target={
                "Arn": start_lambda_arn,
                "RoleArn": scheduler_role_arn,
                "Input": json.dumps({"campaign_id": campaign_id})
            },
            FlexibleTimeWindow={"Mode": "OFF"},
            ActionAfterCompletion="DELETE"  # Auto-delete after execution
        )
        
        print(f"✅ Created scheduler rule: {schedule_name} for {schedule_at}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create scheduler: {e}")
        return False

def trigger_immediate_campaign(campaign_id):
    """Directly invoke start_campaign Lambda for immediate execution"""
    start_lambda_arn = os.environ.get("START_CAMPAIGN_LAMBDA_ARN")
    
    if not start_lambda_arn:
        print(f"Missing start_campaign Lambda ARN")
        return False
    
    try:
        # Extract function name from ARN
        function_name = start_lambda_arn.split(":")[-1]
        
        # Invoke start_campaign Lambda directly
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='Event',  # Async invocation
            Payload=json.dumps({"campaign_id": campaign_id})
        )
        
        print(f"✅ Triggered immediate campaign start: {campaign_id}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to trigger immediate campaign: {e}")
        return False

def create_campaign(event):
    """Create new campaign with full implementation"""
    try:
        user = event['user']  # User already authenticated in handler
        
        try:
            body = json.loads(event.get('body', '{}'))
        except json.JSONDecodeError:
            return _response(400, {"error": "Invalid JSON in request body"})
        
        # Using global enums defined at module level
        
        # Extract data from request
        name = body.get("name")
        emails = body.get("emails")  # List of emails for segment campaigns
        segment_id = body.get("segment_id")  # Optional: existing segment ID
        campaign_type = body.get("type")
        delivery_type = body.get("delivery_type")  # "IND" for individual, "SEG" for segment
        recipient_email = body.get("recipient_email")  # For individual campaigns
        schedule_at = body.get("schedule_at")  # Epoch timestamp or None
        
        # Direct email content is required
        subject = body.get("subject")
        html_body = body.get("html_body")
        from_email = body.get("from_email")
        from_name = body.get("from_name")
        
        # A/B Test specific fields
        ab_test_config = body.get("ab_test_config")
        variations = body.get("variations")
        
        # Validate required fields
        if not name:
            return _response(400, {"error": "name is required"})
        
        if not campaign_type:
            return _response(400, {"error": f"type is required ({CampaignType.IMMEDIATE.value}, {CampaignType.SCHEDULED.value}, or {CampaignType.AB_TEST.value})"})
        
        if campaign_type != CampaignType.AB_TEST.value and not (subject and html_body):
            return _response(400, {"error": "subject and html_body are required for standard campaigns"})
        
        # SECURITY: Sanitize HTML content to prevent injection attacks
        if html_body:
            print(f"🔒 Sanitizing HTML content for campaign: {name}")
            validation_result = sanitize_html_content(html_body)
            
            if not validation_result["is_valid"]:
                print(f"⚠️ HTML validation failed. Blocked elements: {validation_result['blocked_elements']}")
                return _response(400, {
                    "error": "HTML content contains potentially malicious elements",
                    "blocked_elements": validation_result["blocked_elements"],
                    "warnings": validation_result["warnings"]
                })
            
            # Use sanitized HTML
            html_body = validation_result["sanitized_html"]
            
            if validation_result["warnings"]:
                print(f"⚠️ HTML sanitization warnings: {validation_result['warnings']}")
        
        # Validate delivery type and corresponding fields
        if not delivery_type:
            delivery_type = CampaignDeliveryType.SEGMENT.value  # Default to segment-based
        
        if delivery_type == CampaignDeliveryType.INDIVIDUAL.value:
            if not recipient_email:
                return _response(400, {"error": "recipient_email is required for individual campaigns"})
            if emails or segment_id:
                return _response(400, {"error": "emails or segment_id should not be provided for individual campaigns"})
        elif delivery_type == CampaignDeliveryType.SEGMENT.value:
            if recipient_email:
                return _response(400, {"error": "recipient_email should not be provided for segment campaigns"})
            if not emails and not segment_id:
                return _response(400, {"error": "Either emails list or segment_id is required for segment campaigns"})
            if emails and segment_id:
                return _response(400, {"error": "Provide either emails list or segment_id, not both"})
            
            # Validate emails if provided
            if emails:
                if not isinstance(emails, list) or len(emails) == 0:
                    return _response(400, {"error": "emails must be a non-empty list"})
                
                import re
                email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
                invalid_emails = [email for email in emails if not email_pattern.match(email)]
                if invalid_emails:
                    return _response(400, {"error": f"Invalid email addresses: {', '.join(invalid_emails[:5])}"})
        else:
            return _response(400, {"error": f"delivery_type must be '{CampaignDeliveryType.INDIVIDUAL.value}' for individual or '{CampaignDeliveryType.SEGMENT.value}' for segment campaigns"})

        # If emails provided, create a temporary segment
        final_segment_id = segment_id
        if emails and delivery_type == CampaignDeliveryType.SEGMENT.value:
            # Create a temporary segment for this campaign
            final_segment_id = str(uuid.uuid4())
            
            # Store temporary segment
            segments_table = get_segments_table()
            segments_table.put_item(
                Item={
                    'id': final_segment_id,
                    'name': f"Campaign {name} - Recipients",
                    'description': f"Auto-generated segment for campaign: {name}",
                    'emails': list(set(email.lower().strip() for email in emails)),
                    'contact_count': len(set(emails)),
                    'created_at': int(time.time()),
                    'updated_at': int(time.time()),
                    'created_by': user['id'],
                    'owner_id': user['id'],
                    'status': 'active',
                    'temporary': True
                }
            )
            print(f"✅ Created temporary segment {final_segment_id} with {len(set(emails))} emails")
        
        campaign_id = create_campaign_record(
            name=name, 
            segment_id=final_segment_id,
            campaign_type=campaign_type,
            delivery_type=delivery_type,
            recipient_email=recipient_email,
            schedule_at=schedule_at,
            subject=subject,
            html_body=html_body,
            from_email=from_email,
            from_name=from_name,
            owner_id=user['id'],
            ab_test_config=ab_test_config,
            variations=variations
        )
        
        # Dual-path approach based on campaign type:
        if campaign_type == CampaignType.IMMEDIATE.value:  # Immediate campaigns
            print(f"⚡ Immediate execution path for campaign {campaign_id}")
            immediate_triggered = trigger_immediate_campaign(campaign_id)
            
            response_data = {
                "campaign_id": campaign_id,
                "state": CampaignState.PENDING.value,
                "type": campaign_type,
                "delivery_type": delivery_type,
                "recipient_email": recipient_email if delivery_type == CampaignDeliveryType.INDIVIDUAL.value else None,
                "segment_id": final_segment_id if delivery_type == CampaignDeliveryType.SEGMENT.value else None,
                "schedule_at": schedule_at,
                "triggered": immediate_triggered
            }
            
            # Add segment info for segment campaigns
            if delivery_type == CampaignDeliveryType.SEGMENT.value:
                if emails:
                    response_data["recipient_count"] = len(set(emails))
                    response_data["temporary_segment"] = True
                else:
                    response_data["temporary_segment"] = False
        elif campaign_type == CampaignType.SCHEDULED.value:  # Scheduled campaigns
            print(f"📅 Scheduled execution path for campaign {campaign_id}")
            scheduler_created = create_scheduler_rule(campaign_id, schedule_at)
            
            response_data = {
                "campaign_id": campaign_id,
                "state": CampaignState.SCHEDULED.value,
                "type": campaign_type,
                "delivery_type": delivery_type,
                "recipient_email": recipient_email if delivery_type == CampaignDeliveryType.INDIVIDUAL.value else None,
                "segment_id": final_segment_id if delivery_type == CampaignDeliveryType.SEGMENT.value else None,
                "schedule_at": schedule_at,
                "auto_scheduler": scheduler_created
            }
            
            # Add segment info for segment campaigns
            if delivery_type == CampaignDeliveryType.SEGMENT.value:
                if emails:
                    response_data["recipient_count"] = len(set(emails))
                    response_data["temporary_segment"] = True
                else:
                    response_data["temporary_segment"] = False
        elif campaign_type == CampaignType.AB_TEST.value:
            print(f"🧪 A/B Test execution path for campaign {campaign_id}")
            # For A/B tests, we trigger immediate execution (Phase A)
            # The send_worker will handle the split logic
            immediate_triggered = trigger_immediate_campaign(campaign_id)
            
            # We also need to schedule the decision phase (Phase C)
            # But we'll let the send_worker handle creating that scheduler rule 
            # to ensure it only happens if the initial send is successful
            
            response_data = {
                "campaign_id": campaign_id,
                "state": CampaignState.PENDING.value,
                "type": campaign_type,
                "delivery_type": delivery_type,
                "segment_id": final_segment_id,
                "ab_test_config": ab_test_config,
                "triggered": immediate_triggered
            }
            
            if emails:
                response_data["recipient_count"] = len(set(emails))
                response_data["temporary_segment"] = True
            else:
                response_data["temporary_segment"] = False
        else:
            return _response(400, {"error": "Invalid campaign type"})
        
        return _response(201, response_data)
        
    except ValueError as e:
        return _response(401, {"error": f"Authentication failed: {str(e)}"})
    except Exception as e:
        print(f"Error creating campaign: {str(e)}")
        return _response(500, {"error": f"Failed to create campaign: {str(e)}"})

def update_campaign(event):
    """Update existing campaign"""
    try:
        user = event['user']  # User already authenticated in handler
        campaign_id = event['pathParameters']['id']
        
        try:
            body = json.loads(event.get('body', '{}'))
        except json.JSONDecodeError:
            return _response(400, {"error": "Invalid JSON in request body"})
        
        campaigns_table = get_campaigns_table()
        
        # First check if campaign exists and user owns it
        existing = campaigns_table.get_item(Key={'id': campaign_id})
        if 'Item' not in existing:
            return _response(404, {"error": "Campaign not found"})
        
        campaign = existing['Item']
        if campaign.get('owner_id') != user['id']:
            return _response(403, {"error": "Access denied"})
        
        # Don't allow updating campaigns that are already sent or in progress
        if campaign.get('status') in ['sending', 'sent', 'completed']:
            return _response(400, {"error": "Cannot update campaigns that have been sent"})
        
        # Updatable fields
        updatable_fields = ['name', 'subject', 'content', 'schedule_type', 'scheduled_at']
        update_expression = "SET updated_at = :updated_at"
        expression_values = {':updated_at': int(time.time())}
        
        for field in updatable_fields:
            if field in body:
                update_expression += f", {field} = :{field}"
                expression_values[f':{field}'] = body[field]
        
        # Update the campaign
        campaigns_table.update_item(
            Key={'id': campaign_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
        
        # Get updated campaign
        updated = campaigns_table.get_item(Key={'id': campaign_id})
        campaign = convert_decimals(updated['Item'])
        
        return _response(200, {
            "message": "Campaign updated successfully",
            "campaign": campaign
        })
        
    except ValueError as e:
        return _response(401, {"error": f"Authentication failed: {str(e)}"})
    except Exception as e:
        print(f"Error updating campaign: {str(e)}")
        return _response(500, {"error": f"Failed to update campaign: {str(e)}"})

def delete_campaign(event):
    """Delete campaign (soft delete by setting status to 'inactive' then 'deleted')"""
    try:
        user = event['user']  # User already authenticated in handler
        campaign_id = event['pathParameters']['id']
        
        campaigns_table = get_campaigns_table()
        
        # First check if campaign exists and user owns it
        existing = campaigns_table.get_item(Key={'id': campaign_id})
        if 'Item' not in existing:
            return _response(404, {"error": "Campaign not found"})
        
        campaign = existing['Item']
        if campaign.get('owner_id') != user['id']:
            return _response(403, {"error": "Access denied"})
        
        # Don't allow deleting campaigns that are currently sending
        if campaign.get('status') == 'sending':
            return _response(400, {"error": "Cannot delete campaigns that are currently sending"})
        
        # Two-stage delete: 
        # 1. Any Active state -> Inactive (Trash)
        # 2. Inactive (Trash) -> Deleted (DB-only)
        current_status = (campaign.get('status') or "").upper()
        
        # Define statuses that are considered "Active/Live"
        # If it's anything other than INACTIVE (I) or DELETED (D), it goes to Trash (I)
        if current_status not in [CampaignStatus.INACTIVE.value, CampaignStatus.DELETED.value]:
            new_status = CampaignStatus.INACTIVE.value
            message = "Campaign moved to trash"
        else:
            # It's already in Trash or already Deleted
            new_status = CampaignStatus.DELETED.value
            message = "Campaign deleted permanently"

        # Soft delete by updating status
        campaigns_table.update_item(
            Key={'id': campaign_id},
            UpdateExpression="SET #status = :status, updated_at = :updated_at",
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': new_status,
                ':updated_at': int(time.time())
            }
        )
        
        return _response(200, {"message": message, "status": new_status})
        
    except ValueError as e:
        return _response(401, {"error": f"Authentication failed: {str(e)}"})
    except Exception as e:
        print(f"Error deleting campaign: {str(e)}")
        return _response(500, {"error": f"Failed to delete campaign: {str(e)}"})

def calculate_unique_opens(events):
    """Calculate unique opens from events (including implied opens from clicks)"""
    try:
        unique_opens = set()
        unique_clicks = set()
        
        for event in events:
            email = event.get('email')
            if not email:
                continue
                
            if event.get('type') == EventType.OPEN.value:
                unique_opens.add(email)
            elif event.get('type') == EventType.CLICK.value:
                unique_clicks.add(email)
                
        # If a user clicked, they must have opened. Add them to opens.
        unique_opens.update(unique_clicks)
        
        return len(unique_opens)
    except Exception as e:
        print(f"Error calculating unique opens: {e}")
        return 0

def calculate_unique_clicks(events):
    """Calculate unique clicks from events"""
    try:
        unique_clicks = set()
        for event in events:
            if event.get('type') == EventType.CLICK.value:
                email = event.get('email')
                if email:
                    unique_clicks.add(email)
        return len(unique_clicks)
    except Exception as e:
        print(f"Error calculating unique clicks: {e}")
        return 0

def calculate_unique_recipients(events):
    """Calculate unique recipients from all events"""
    try:
        unique_recipients = set()
        for event in events:
            email = event.get('email')
            if email:
                unique_recipients.add(email)
        return len(unique_recipients)
    except Exception as e:
        print(f"Error calculating unique recipients: {e}")
        return 0

def calculate_top_clicked_links(events, top_n=5):
    """Calculate top clicked links from events"""
    try:
        link_counts = {}
        for event in events:
            if event.get('type') == EventType.CLICK.value:
                raw_data = event.get('raw')
                if not raw_data:
                    continue
                    
                raw_data = raw_data if isinstance(raw_data, dict) else json.loads(raw_data)
                link_id = raw_data.get('link_id')
                if link_id:
                    link_counts[link_id] = link_counts.get(link_id, 0) + 1
        
        # Sort links by count and return top N
        sorted_links = sorted(link_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"url": link, "clicks": count} for link, count in sorted_links[:top_n]]
    except Exception as e:
        print(f"Error calculating top clicked links: {e}")
        return []
    sorted_links = sorted(link_counts.items(), key=lambda x: x[1], reverse=True)
    return [{"link_id": url, "click_count": count} for url, count in sorted_links[:top_n]]

def calculate_avg_time_to_open(events):
    """Calculate average time-to-open from sent to open events"""
    try:
        # First pass: collect all sent times
        sent_times = {
            e.get('email'): e.get('created_at') 
            for e in events 
            if e.get('type') == EventType.SENT.value and e.get('email') and e.get('created_at') is not None
        }
        
        open_times = []
        
        for event in events:
            if event.get('type') == EventType.OPEN.value:
                email = event.get('email')
                created_at = event.get('created_at')
                if email and email in sent_times and created_at is not None:
                    # Ensure we don't get negative times due to clock skew
                    time_diff = max(0, created_at - sent_times[email])
                    open_times.append(time_diff)
        
        if not open_times:
            return None
        
        average_time = sum(open_times) / len(open_times)
        return round(average_time, 2)
    except Exception as e:
        print(f"Error calculating avg time to open: {e}")
        return None

def calculate_avg_time_to_click(events):
    """Calculate average time-to-click from sent to click events"""
    try:
        # First pass: collect all sent times
        sent_times = {
            e.get('email'): e.get('created_at') 
            for e in events 
            if e.get('type') == EventType.SENT.value and e.get('email') and e.get('created_at') is not None
        }
        
        click_times = []
        
        for event in events:
            if event.get('type') == EventType.CLICK.value:
                email = event.get('email')
                created_at = event.get('created_at')
                if email and email in sent_times and created_at is not None:
                    # Ensure we don't get negative times due to clock skew
                    time_diff = max(0, created_at - sent_times[email])
                    click_times.append(time_diff)
        
        if not click_times:
            return None
        
        average_time = sum(click_times) / len(click_times)
        return round(average_time, 2)
    except Exception as e:
        print(f"Error calculating avg time to click: {e}")
        return None

def get_campaign_events(event):
    """Get analytics/events for a specific campaign with time range filtering and distribution data"""
    try:
        user = event['user']  # User already authenticated in handler
        campaign_id = event['pathParameters']['id']
        
        campaigns_table = get_campaigns_table()
        events_table = get_events_table()
        
        # First verify campaign exists and user owns it
        campaign_response = campaigns_table.get_item(Key={'id': campaign_id})
        if 'Item' not in campaign_response:
            return _response(404, {"error": "Campaign not found"})
        
        campaign = campaign_response['Item']
        if campaign.get('owner_id') != user['id']:
            return _response(403, {"error": "Access denied"})
        
        # Get query parameters
        query_params = event.get('queryStringParameters') or {}
        limit = int(query_params.get('limit', 1000))
        limit = min(limit, 1000)  # Max 1000 events per request
        from_epoch = query_params.get('from_epoch')
        to_epoch = query_params.get('to_epoch')
        country_code = query_params.get('country_code')
        variation_id = query_params.get('variation_id')  # A/B test variation filter
        
        # Build query parameters for DynamoDB
        query_kwargs = {
            'IndexName': 'campaign_index',
            'KeyConditionExpression': Key('campaign_id').eq(campaign_id),
            'Limit': limit,
            'ScanIndexForward': False  # Most recent first
        }
        
        # Add time range filtering if provided
        filter_conditions = []
        
        if from_epoch:
            try:
                from_timestamp = int(from_epoch)
                filter_conditions.append(Attr('created_at').gte(from_timestamp))
            except ValueError:
                return _response(400, {"error": "Invalid from_epoch format. Must be Unix timestamp"})
        
        if to_epoch:
            try:
                to_timestamp = int(to_epoch)
                filter_conditions.append(Attr('created_at').lte(to_timestamp))
            except ValueError:
                return _response(400, {"error": "Invalid to_epoch format. Must be Unix timestamp"})
        
        if country_code:
            filter_conditions.append(Attr('raw').contains(f'"country_code": "{country_code}"'))
        
        # Combine filter conditions if any exist
        if filter_conditions:
            if len(filter_conditions) == 1:
                query_kwargs['FilterExpression'] = filter_conditions[0]
            else:
                # Combine multiple conditions with AND
                combined_filter = filter_conditions[0]
                for condition in filter_conditions[1:]:
                    combined_filter = combined_filter & condition
                query_kwargs['FilterExpression'] = combined_filter
        
        events_response = events_table.query(**query_kwargs)
        events = convert_decimals(events_response.get('Items', []))
        
        # Filter by variation_id in Python if specified (more reliable than DynamoDB contains)
        if variation_id:
            filtered_events = []
            for event in events:
                raw_data = event.get('raw', '{}')
                try:
                    # Parse the raw JSON string
                    if isinstance(raw_data, str):
                        metadata = json.loads(raw_data)
                    else:
                        metadata = raw_data
                    
                    # Check if variation_id matches
                    if metadata.get('variation_id') == variation_id:
                        filtered_events.append(event)
                except (json.JSONDecodeError, AttributeError):
                    # Skip events with invalid JSON
                    continue
            
            events = filtered_events
        
        # Calculate summary statistics
        event_counts = {}
        
        # Separate distributions for opens and clicks
        # Opens come through proxies, so device/browser/OS data is not reliable
        # Only clicks provide accurate device information
        open_country_distribution = {}
        
        click_os_distribution = {}
        click_device_distribution = {}
        click_browser_distribution = {}
        click_country_distribution = {}
        
        for event in events:
            # Event type counts
            event_type = event.get('type', EventType.UNKNOWN.value)
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

            raw_data = event.get('raw')
            raw_data = raw_data if isinstance(raw_data, dict) else json.loads(raw_data)

            if event_type == EventType.SENT.value:
                continue

            # Extract metadata
            country_info = raw_data.get('country_code', 'Unknown')
            
            # Only track device/browser/OS for clicks (reliable data)
            if event_type == EventType.CLICK.value:
                os_info = raw_data.get('os', 'Unknown')
                device_info = raw_data.get('device_type', 'Unknown')
                browser_info = raw_data.get('browser', 'Unknown')
                
                click_os_distribution[os_info] = click_os_distribution.get(os_info, 0) + 1
                click_device_distribution[device_info] = click_device_distribution.get(device_info, 0) + 1
                click_browser_distribution[browser_info] = click_browser_distribution.get(browser_info, 0) + 1
                click_country_distribution[country_info] = click_country_distribution.get(country_info, 0) + 1
            
            # Track country for opens (still useful for geographic distribution)
            elif event_type == EventType.OPEN.value:
                open_country_distribution[country_info] = open_country_distribution.get(country_info, 0) + 1
        
        # Format distributions for frontend charts
        def format_distribution(distribution_dict, max_items=10):
            """Format distribution data for frontend charts with 'Other' category for long tail"""
            sorted_items = sorted(distribution_dict.items(), key=lambda x: x[1], reverse=True)
            
            if len(sorted_items) <= max_items:
                return [{"name": name, "value": count} for name, count in sorted_items]
            
            top_items = sorted_items[:max_items-1]
            other_count = sum(count for _, count in sorted_items[max_items-1:])
            
            result = [{"name": name, "value": count} for name, count in top_items]
            if other_count > 0:
                result.append({"name": "Other", "value": other_count})
            
            return result
        
        # Format event counts for better visualization
        event_types_summary = []
        for event_type, count in sorted(event_counts.items(), key=lambda x: x[1], reverse=True):
            event_types_summary.append({
                "event_type": event_type,
                "count": count,
                "percentage": round((count / len(events) * 100), 2) if events else 0
            })


        # Calculate unique recipients and opens
        unique_recipients = calculate_unique_recipients(events)
        unique_opens_count = calculate_unique_opens(events)
        
        # Ensure total opens is at least equal to unique opens (handling implied opens)
        event_counts['open'] = max(event_counts.get('open', 0), unique_opens_count)

        return _response(200, {
            "events": events,
            "summary": {
                "total_events": len(events),
                "event_counts": event_counts,
                "event_types_breakdown": event_types_summary,
                "campaign_id": campaign_id,
                "campaign_name": campaign.get('name'),
                "time_range": {
                    "from_epoch": from_epoch,
                    "to_epoch": to_epoch
                },
                'unique_opens': unique_opens_count,
                'unique_clicks': calculate_unique_clicks(events),
                'unique_recipients': calculate_unique_recipients(events),
                'top_clicked_links': calculate_top_clicked_links(events),
                'avg_time_to_open': calculate_avg_time_to_open(events),
                'avg_time_to_click': calculate_avg_time_to_click(events)
            },
            "distributions": {
                "open_data": {
                    "country_distribution": format_distribution(open_country_distribution)
                },
                "click_data": {
                    "os_distribution": format_distribution(click_os_distribution),
                    "device_distribution": format_distribution(click_device_distribution),
                    "browser_distribution": format_distribution(click_browser_distribution),
                    "country_distribution": format_distribution(click_country_distribution)
                }
            },
            "has_more": 'LastEvaluatedKey' in events_response
        })
        
    except ValueError as e:
        return _response(401, {"error": f"Authentication failed: {str(e)}"})
    except Exception as e:
        print(f"Error getting campaign events: {str(e)}")
        return _response(500, {"error": f"Failed to get campaign events: {str(e)}"})

def lambda_handler(event, context):
    """Main handler for campaigns API"""
    print(f"Campaigns API Handler: {json.dumps(event, default=str)}")
    
    # Get HTTP method and path
    http_method = event.get('requestContext', {}).get('http', {}).get('method') or event.get('httpMethod', 'GET')
    path = event.get('rawPath') or event.get('path', '')
    path_params = event.get('pathParameters') or {}
    
    print(f"DEBUG - HTTP Method: {http_method}")
    print(f"DEBUG - Path: {path}")
    print(f"DEBUG - Path Params: {path_params}")
    
    # Handle CORS preflight
    if http_method == 'OPTIONS':
        return _response(200, {})
    
    # Authenticate user from API Gateway authorizer context
    try:
        user = get_user_from_context(event)
        # Add user to event for use in route handlers
        event['user'] = user
    except Exception as e:
        return _response(401, {"error": f"Authentication failed: {str(e)}"})
    
    try:
        # Route requests based on path and method
        if path == '/v1/campaigns' or path == '/campaigns':
            if http_method == 'GET':
                return list_campaigns(event)
            elif http_method == 'POST':
                return create_campaign(event)
        
        elif path.startswith('/v1/campaigns/') or path.startswith('/campaigns/'):
            campaign_id = path_params.get('id')
            if not campaign_id:
                return _response(400, {"error": "Campaign ID is required"})
            
            if path.endswith('/events'):
                if http_method == 'GET':
                    return get_campaign_events(event)
            else:
                if http_method == 'GET':
                    return get_campaign(event)
                elif http_method == 'PUT':
                    return update_campaign(event)
                elif http_method == 'DELETE':
                    return delete_campaign(event)
        
        # Route not found
        return _response(404, {"error": "Route not found"})
        
    except Exception as e:
        print(f"Error in campaigns API handler: {e}")
        return _response(500, {"error": "Internal server error"})