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
    EventType, EngagementLevel
)

# ================================
# CONSTANTS
# ================================

# Default values
DEFAULT_FROM_EMAIL = "no-reply@thesentinel.site"
DEFAULT_FROM_NAME = "Sentinel"



class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal objects from DynamoDB"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj % 1 == 0:
                return int(obj)
            else:
                return float(obj)
        return super(DecimalEncoder, self).default(obj)



def calculate_temporal_analytics(events):
    """Calculate time-based engagement analytics"""
    if not events:
        return {
            "hourly_engagement": {"peak_hours": [], "engagement_by_hour": []},
            "daily_patterns": {"best_day": None, "engagement_by_day": []},
            "response_times": {"avg_time_to_open": 0, "avg_time_to_click": 0}
        }
    
    from collections import defaultdict
    import calendar
    
    # Hourly engagement analysis
    hourly_stats = defaultdict(lambda: {"opens": 0, "clicks": 0, "total": 0})
    daily_stats = defaultdict(lambda: {"opens": 0, "clicks": 0, "total": 0})
    
    for event in events:
        timestamp = event.get('timestamp')
        event_type = event.get('event_type', EventType.UNKNOWN.value)
        
        if timestamp:
            dt = datetime.fromtimestamp(timestamp, timezone.utc)
            hour = dt.hour
            day_name = calendar.day_name[dt.weekday()]
            
            hourly_stats[hour]["total"] += 1
            daily_stats[day_name]["total"] += 1
            
            if event_type == EventType.OPEN.value:
                hourly_stats[hour]["opens"] += 1
                daily_stats[day_name]["opens"] += 1
            elif event_type == EventType.CLICK.value:
                hourly_stats[hour]["clicks"] += 1 
                daily_stats[day_name]["clicks"] += 1
    
    # Format hourly data
    engagement_by_hour = []
    for hour in range(24):
        stats = hourly_stats[hour]
        engagement_score = (stats["opens"] + stats["clicks"] * 2)  # Clicks weighted higher
        engagement_by_hour.append({
            "hour": hour,
            "opens": stats["opens"],
            "clicks": stats["clicks"],
            "engagement_score": engagement_score
        })
    
    # Find peak hours (top 3)
    peak_hours = sorted(engagement_by_hour, key=lambda x: x["engagement_score"], reverse=True)[:3]
    peak_hour_numbers = [h["hour"] for h in peak_hours if h["engagement_score"] > 0]
    
    # Format daily data
    engagement_by_day = []
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for day in day_order:
        stats = daily_stats[day]
        engagement_score = (stats["opens"] + stats["clicks"] * 2)
        engagement_by_day.append({
            "day": day,
            "opens": stats["opens"],
            "clicks": stats["clicks"], 
            "engagement_score": engagement_score
        })
    
    # Find best day
    best_day_data = max(engagement_by_day, key=lambda x: x["engagement_score"]) if engagement_by_day else None
    best_day = best_day_data["day"] if best_day_data and best_day_data["engagement_score"] > 0 else None
    
    return {
        "hourly_engagement": {
            "peak_hours": peak_hour_numbers,
            "engagement_by_hour": engagement_by_hour,
            "optimal_send_time": f"{peak_hour_numbers[0]:02d}:00" if peak_hour_numbers else None
        },
        "daily_patterns": {
            "best_day": best_day,
            "engagement_by_day": engagement_by_day
        },
        "response_times": {
            "avg_time_to_open": None,  # Would need send timestamp to calculate
            "avg_time_to_click": None,  # Would need open timestamp to calculate 
            "total_analysis_period": len(events)
        }
    }

def calculate_engagement_metrics(events, event_counts):
    """Calculate advanced engagement metrics"""
    if not events or not event_counts:
        return {
            "click_to_open_rate": 0,
            "unique_engagement_rate": 0,
            "engagement_quality_score": 0,
            "bounce_rate": 0
        }
    
    opens = event_counts.get(EventType.OPEN.value, 0)
    clicks = event_counts.get(EventType.CLICK.value, 0)  
    bounces = event_counts.get(EventType.BOUNCE.value, 0)
    total_events = len(events)
    
    # Click-to-Open Rate (CTOR) - industry standard metric
    click_to_open_rate = round((clicks / opens * 100), 2) if opens > 0 else 0
    
    # Unique engagement rate (opens + clicks / total events)
    unique_engagement_rate = round(((opens + clicks) / total_events * 100), 2) if total_events > 0 else 0
    
    # Engagement quality score (weighted metric)
    engagement_quality_score = round((opens * 1 + clicks * 3 - bounces * 2) / max(total_events, 1) * 10, 1)
    engagement_quality_score = max(0, min(10, engagement_quality_score))  # Clamp between 0-10
    
    # Bounce rate
    bounce_rate = round((bounces / total_events * 100), 2) if total_events > 0 else 0
    
    return {
        "click_to_open_rate": click_to_open_rate,
        "unique_engagement_rate": unique_engagement_rate, 
        "engagement_quality_score": engagement_quality_score,
        "bounce_rate": bounce_rate,
        "advanced_metrics": {
            "total_interactions": opens + clicks,
            "interaction_diversity": len([k for k, v in event_counts.items() if v > 0]),
            "engagement_intensity": round((clicks + opens) / max(len(set(e.get('recipient_email', '') for e in events if e.get('recipient_email'))), 1), 2)
        }
    }

def calculate_recipient_insights(events):
    """Calculate recipient behavior insights"""
    if not events:
        return {
            "unique_recipients": 0,
            "engagement_segments": {
                "highly_engaged": {"count": 0, "percentage": 0},
                "moderately_engaged": {"count": 0, "percentage": 0}, 
                "low_engaged": {"count": 0, "percentage": 0}
            },
            "top_recipients": []
        }
    
    from collections import defaultdict, Counter
    
    # Track recipient activity
    recipient_activity = defaultdict(lambda: {"opens": 0, "clicks": 0, "events": 0, "last_activity": 0})
    
    for event in events:
        recipient = event.get('recipient_email', EventType.UNKNOWN.value)
        event_type = event.get('event_type', EventType.UNKNOWN.value)
        timestamp = event.get('timestamp', 0)
        
        recipient_activity[recipient]["events"] += 1
        recipient_activity[recipient]["last_activity"] = max(recipient_activity[recipient]["last_activity"], timestamp)
        
        if event_type == EventType.OPEN.value:
            recipient_activity[recipient]["opens"] += 1
        elif event_type == EventType.CLICK.value:
            recipient_activity[recipient]["clicks"] += 1
    
    # Calculate engagement scores for each recipient
    recipient_scores = []
    for recipient, activity in recipient_activity.items():
        if recipient != EventType.UNKNOWN.value:
            # Engagement score: opens * 1 + clicks * 3
            score = activity["opens"] * 1 + activity["clicks"] * 3
            recipient_scores.append({
                "recipient": recipient[:50] + "..." if len(recipient) > 50 else recipient,  # Truncate for privacy
                "engagement_score": score,
                "opens": activity["opens"],
                "clicks": activity["clicks"],
                "total_events": activity["events"],
                "last_activity": activity["last_activity"]
            })
    
    # Sort by engagement score
    recipient_scores.sort(key=lambda x: x["engagement_score"], reverse=True)
    
    # Segment recipients by engagement level
    total_recipients = len(recipient_scores)
    if total_recipients > 0:
        # Define thresholds (can be customized)
        high_threshold = 5  # 5+ engagement points
        medium_threshold = 2  # 2-4 engagement points
        
        highly_engaged = [r for r in recipient_scores if r["engagement_score"] >= high_threshold]
        moderately_engaged = [r for r in recipient_scores if medium_threshold <= r["engagement_score"] < high_threshold]
        low_engaged = [r for r in recipient_scores if r["engagement_score"] < medium_threshold]
    else:
        highly_engaged = moderately_engaged = low_engaged = []
    
    return {
        "unique_recipients": total_recipients,
        "engagement_segments": {
            "highly_engaged": {
                "count": len(highly_engaged),
                "percentage": round(len(highly_engaged) / max(total_recipients, 1) * 100, 1)
            },
            "moderately_engaged": {
                "count": len(moderately_engaged),
                "percentage": round(len(moderately_engaged) / max(total_recipients, 1) * 100, 1)
            },
            "low_engaged": {
                "count": len(low_engaged), 
                "percentage": round(len(low_engaged) / max(total_recipients, 1) * 100, 1)
            }
        },
        "top_recipients": recipient_scores[:10],  # Top 10 most engaged
        "recipient_stats": {
            "avg_opens_per_recipient": round(sum(r["opens"] for r in recipient_scores) / max(total_recipients, 1), 2),
            "avg_clicks_per_recipient": round(sum(r["clicks"] for r in recipient_scores) / max(total_recipients, 1), 2),
            "multi_event_recipients": len([r for r in recipient_scores if r["total_events"] > 1])
        }
    }

# Import common utilities
from common import _response, convert_decimals, get_user_from_context, get_campaigns_table, get_events_table, get_segments_table, parse_user_agent

# DynamoDB clients
lambda_client = boto3.client('lambda', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

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
        
        # Add status filter if provided
        if status_filter:
            query_params['FilterExpression'] = Attr('status').eq(status_filter)
        
        response = campaigns_table.query(**query_params)
        campaigns = convert_decimals(response.get('Items', []))
        
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
                   schedule_at=None, subject=None, html_body=None, from_email=None, from_name=None, owner_id=None):
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
    else:
        raise ValueError(f"Invalid campaign_type: {campaign_type}. Must be '{CampaignType.IMMEDIATE.value}' or '{CampaignType.SCHEDULED.value}'")
    
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
        "metadata": {}  # For additional custom fields
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
        
        # Validate required fields
        if not name:
            return _response(400, {"error": "name is required"})
        
        if not campaign_type:
            return _response(400, {"error": f"type is required ({CampaignType.IMMEDIATE.value} for immediate, {CampaignType.SCHEDULED.value} for scheduled)"})
        
        if not (subject and html_body):
            return _response(400, {"error": "subject and html_body are required"})
        
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
            owner_id=user['id']
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
                "execution_path": "immediate",
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
                "execution_path": CampaignDeliveryType.SCHEDULED.value,
                "auto_scheduler": scheduler_created
            }
            
            # Add segment info for segment campaigns
            if delivery_type == CampaignDeliveryType.SEGMENT.value:
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
    """Delete campaign (soft delete by setting status to 'deleted')"""
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
        
        # Soft delete by updating status
        campaigns_table.update_item(
            Key={'id': campaign_id},
            UpdateExpression="SET #status = :status, updated_at = :updated_at",
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': CampaignStatus.DELETED.value,
                ':updated_at': int(time.time())
            }
        )
        
        return _response(200, {"message": "Campaign deleted successfully"})
        
    except ValueError as e:
        return _response(401, {"error": f"Authentication failed: {str(e)}"})
    except Exception as e:
        print(f"Error deleting campaign: {str(e)}")
        return _response(500, {"error": f"Failed to delete campaign: {str(e)}"})

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
                filter_conditions.append(Attr('timestamp').gte(from_timestamp))
            except ValueError:
                return _response(400, {"error": "Invalid from_epoch format. Must be Unix timestamp"})
        
        if to_epoch:
            try:
                to_timestamp = int(to_epoch)
                filter_conditions.append(Attr('timestamp').lte(to_timestamp))
            except ValueError:
                return _response(400, {"error": "Invalid to_epoch format. Must be Unix timestamp"})
        
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
        
        # Calculate summary statistics
        event_counts = {}
        os_distribution = {}
        device_distribution = {}
        browser_distribution = {}
        ip_distribution = {}
        
        for event in events:
            # Event type counts
            event_type = event.get('event_type', EventType.UNKNOWN.value)
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            # Extract user agent and IP data for distributions
            user_agent = event.get('user_agent', '')
            ip_address = event.get('ip_address', 'unknown')
            
            # Parse user agent for OS, device, and browser info
            user_agent_info = parse_user_agent(user_agent)
            os_info = user_agent_info['os']
            device_info = user_agent_info['device_type']
            browser_info = user_agent_info['browser']
            
            # Update distributions
            os_distribution[os_info] = os_distribution.get(os_info, 0) + 1
            device_distribution[device_info] = device_distribution.get(device_info, 0) + 1
            browser_distribution[browser_info] = browser_distribution.get(browser_info, 0) + 1
            ip_distribution[ip_address] = ip_distribution.get(ip_address, 0) + 1
        
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
        
        # Calculate temporal analytics (Phase 1 enhancement)
        temporal_analytics = calculate_temporal_analytics(events)
        
        # Calculate advanced engagement metrics
        engagement_metrics = calculate_engagement_metrics(events, event_counts)
        
        # Calculate recipient insights
        recipient_insights = calculate_recipient_insights(events)

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
                }
            },
            "distributions": {
                "os_distribution": format_distribution(os_distribution),
                "device_distribution": format_distribution(device_distribution),
                "browser_distribution": format_distribution(browser_distribution),
                "ip_distribution": format_distribution(ip_distribution, max_items=15)
            },
            "temporal_analytics": temporal_analytics,
            "engagement_metrics": engagement_metrics,
            "recipient_insights": recipient_insights,
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