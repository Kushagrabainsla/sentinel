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

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal objects from DynamoDB"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj % 1 == 0:
                return int(obj)
            else:
                return float(obj)
        return super(DecimalEncoder, self).default(obj)

def convert_decimals(obj):
    """Recursively convert Decimal objects to int/float in DynamoDB items"""
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj

# DynamoDB clients
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
lambda_client = boto3.client('lambda', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

def get_campaigns_table():
    """Get campaigns table"""
    table_name = os.environ.get('DYNAMODB_CAMPAIGNS_TABLE')
    if not table_name:
        raise RuntimeError('DYNAMODB_CAMPAIGNS_TABLE environment variable not set')
    return dynamodb.Table(table_name)

def get_events_table():
    """Get events table"""
    table_name = os.environ.get('DYNAMODB_EVENTS_TABLE')
    if not table_name:
        raise RuntimeError('DYNAMODB_EVENTS_TABLE environment variable not set')
    return dynamodb.Table(table_name)

def get_user_from_context(event):
    """Extract user information from API Gateway v2 authorizer context"""
    try:
        print(f"DEBUG: Full event context: {json.dumps(event.get('requestContext', {}), default=str)}")
        
        request_context = event.get('requestContext', {})
        authorizer_data = request_context.get('authorizer', {})
        lambda_context = authorizer_data.get('lambda', {})
        context = lambda_context if lambda_context else authorizer_data
        
        print(f"DEBUG: Authorizer context: {json.dumps(context, default=str)}")
        
        if not context:
            raise ValueError("No authorizer context found")
        
        user = {
            'id': context.get('user_id'),
            'email': context.get('user_email'),
            'status': context.get('user_status', 'active')
        }
        
        if not user['id'] or not user['email']:
            raise ValueError(f"Invalid user context from authorizer. Context keys: {list(context.keys())}")
            
        print(f"DEBUG: Extracted user: {user}")
        return user
        
    except Exception as e:
        print(f"ERROR: Context extraction failed: {str(e)}")
        raise ValueError(f"Failed to extract user from context: {str(e)}")

def _response(status_code, body, headers=None):
    """Helper function to create API Gateway response"""
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization,X-API-Key",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": json.dumps(body, cls=DecimalEncoder)
    }

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
    
    # Campaign Type Enums
    class CampaignType:
        IMMEDIATE = "I"  # Immediate execution
        SCHEDULED = "S"  # Scheduled execution

    # Campaign Delivery Mechanism Enums
    class CampaignDeliveryType:
        INDIVIDUAL = "IND"   # Single recipient
        SEGMENT = "SEG"      # Segment-based (multiple recipients)

    # Campaign State Enums
    class CampaignState:
        SCHEDULED = "SC"  # Scheduled for future execution
        PENDING = "P"     # Pending immediate execution
        SENDING = "SE"    # Currently sending
        DONE = "D"        # Completed
        FAILED = "F"      # Failed

    # Campaign Status Enums
    class CampaignStatus:
        ACTIVE = "A"      # Active campaign
        INACTIVE = "I"    # Inactive campaign
    
    campaigns_table = get_campaigns_table()
    campaign_id = str(uuid.uuid4())
    current_timestamp = int(time.time())
    
    # Validate delivery_type and corresponding fields
    if not delivery_type:
        delivery_type = CampaignDeliveryType.SEGMENT  # Default to segment-based
    
    if delivery_type == CampaignDeliveryType.INDIVIDUAL:
        if not recipient_email:
            raise ValueError("recipient_email is required for individual campaigns")
        if segment_id:
            raise ValueError("segment_id should not be provided for individual campaigns")
    elif delivery_type == CampaignDeliveryType.SEGMENT:
        if recipient_email:
            raise ValueError("recipient_email should not be provided for segment campaigns")
        if not segment_id:
            raise ValueError("segment_id is required for segment campaigns")
    else:
        raise ValueError(f"Invalid delivery_type: {delivery_type}. Must be '{CampaignDeliveryType.INDIVIDUAL}' or '{CampaignDeliveryType.SEGMENT}'")
    
    # Validate campaign_type and schedule_at requirements
    if campaign_type == CampaignType.SCHEDULED:
        if not schedule_at:
            raise ValueError("schedule_at is required for scheduled campaigns")
    elif campaign_type == CampaignType.IMMEDIATE:
        if schedule_at:
            raise ValueError("schedule_at should not be provided for immediate campaigns")
    else:
        raise ValueError(f"Invalid campaign_type: {campaign_type}. Must be '{CampaignType.IMMEDIATE}' or '{CampaignType.SCHEDULED}'")
    
    item = {
        "id": campaign_id,
        "name": name,
        "created_at": current_timestamp,
        "updated_at": current_timestamp,
        "type": campaign_type,
        "delivery_type": delivery_type,
        "email_subject": subject or "",
        "email_body": html_body or "",
        "from_email": from_email or "noreply@thesentinel.site",
        "from_name": from_name or "Sentinel",
        "segment_id": segment_id,
        "recipient_email": recipient_email,
        "schedule_at": schedule_at,
        "state": CampaignState.SCHEDULED if campaign_type == CampaignType.SCHEDULED else CampaignState.PENDING,
        "status": CampaignStatus.ACTIVE,
        "owner_id": owner_id,
        "tags": [],  # For categorization and filtering
        "metadata": {}  # For additional custom fields
    }
    
    try:
        campaigns_table.put_item(Item=item)
    except ClientError:
        raise
    return campaign_id

def get_segments_table():
    """Get segments table"""
    table_name = os.environ.get('DYNAMODB_SEGMENTS_TABLE')
    if not table_name:
        raise RuntimeError('DYNAMODB_SEGMENTS_TABLE environment variable not set')
    return dynamodb.Table(table_name)

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
        
        # Campaign Type Enums
        class CampaignType:
            IMMEDIATE = "I"  # Immediate execution
            SCHEDULED = "S"  # Scheduled execution

        # Campaign Delivery Mechanism Enums
        class CampaignDeliveryType:
            INDIVIDUAL = "IND"   # Single recipient
            SEGMENT = "SEG"      # Segment-based (multiple recipients)

        # Campaign State Enums
        class CampaignState:
            SCHEDULED = "SC"  # Scheduled for future execution
            PENDING = "P"     # Pending immediate execution
            SENDING = "SE"    # Currently sending
            DONE = "D"        # Completed
            FAILED = "F"      # Failed
        
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
            return _response(400, {"error": f"type is required ({CampaignType.IMMEDIATE} for immediate, {CampaignType.SCHEDULED} for scheduled)"})
        
        if not (subject and html_body):
            return _response(400, {"error": "subject and html_body are required"})
        
        # Validate delivery type and corresponding fields
        if not delivery_type:
            delivery_type = CampaignDeliveryType.SEGMENT  # Default to segment-based
        
        if delivery_type == CampaignDeliveryType.INDIVIDUAL:
            if not recipient_email:
                return _response(400, {"error": "recipient_email is required for individual campaigns"})
            if emails or segment_id:
                return _response(400, {"error": "emails or segment_id should not be provided for individual campaigns"})
        elif delivery_type == CampaignDeliveryType.SEGMENT:
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
            return _response(400, {"error": f"delivery_type must be '{CampaignDeliveryType.INDIVIDUAL}' for individual or '{CampaignDeliveryType.SEGMENT}' for segment campaigns"})

        # If emails provided, create a temporary segment
        final_segment_id = segment_id
        if emails and delivery_type == CampaignDeliveryType.SEGMENT:
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
        if campaign_type == CampaignType.IMMEDIATE:  # Immediate campaigns
            print(f"⚡ Immediate execution path for campaign {campaign_id}")
            immediate_triggered = trigger_immediate_campaign(campaign_id)
            
            response_data = {
                "campaign_id": campaign_id,
                "state": CampaignState.PENDING,
                "type": campaign_type,
                "delivery_type": delivery_type,
                "recipient_email": recipient_email if delivery_type == CampaignDeliveryType.INDIVIDUAL else None,
                "segment_id": final_segment_id if delivery_type == CampaignDeliveryType.SEGMENT else None,
                "schedule_at": schedule_at,
                "execution_path": "immediate",
                "triggered": immediate_triggered
            }
            
            # Add segment info for segment campaigns
            if delivery_type == CampaignDeliveryType.SEGMENT:
                if emails:
                    response_data["recipient_count"] = len(set(emails))
                    response_data["temporary_segment"] = True
                else:
                    response_data["temporary_segment"] = False
        elif campaign_type == CampaignType.SCHEDULED:  # Scheduled campaigns
            print(f"📅 Scheduled execution path for campaign {campaign_id}")
            scheduler_created = create_scheduler_rule(campaign_id, schedule_at)
            
            response_data = {
                "campaign_id": campaign_id,
                "state": CampaignState.SCHEDULED,
                "type": campaign_type,
                "delivery_type": delivery_type,
                "recipient_email": recipient_email if delivery_type == CampaignDeliveryType.INDIVIDUAL else None,
                "segment_id": final_segment_id if delivery_type == CampaignDeliveryType.SEGMENT else None,
                "schedule_at": schedule_at,
                "execution_path": "scheduled",
                "auto_scheduler": scheduler_created
            }
            
            # Add segment info for segment campaigns
            if delivery_type == CampaignDeliveryType.SEGMENT:
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
                ':status': 'deleted',
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
    """Get analytics/events for a specific campaign"""
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
        
        # Get events for this campaign
        query_params = event.get('queryStringParameters') or {}
        limit = int(query_params.get('limit', 100))
        limit = min(limit, 1000)  # Max 1000 events per request
        
        events_response = events_table.query(
            IndexName='campaign_index',
            KeyConditionExpression=Key('campaign_id').eq(campaign_id),
            Limit=limit,
            ScanIndexForward=False  # Most recent first
        )
        
        events = convert_decimals(events_response.get('Items', []))
        
        # Calculate summary statistics
        event_counts = {}
        for event in events:
            event_type = event.get('event_type', 'unknown')
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return _response(200, {
            "events": events,
            "summary": {
                "total_events": len(events),
                "event_counts": event_counts,
                "campaign_id": campaign_id,
                "campaign_name": campaign.get('name')
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