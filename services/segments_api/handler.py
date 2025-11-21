import json
import os
import sys
import time
import uuid
from datetime import datetime
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

# Import common utilities and enums
from common import _response, convert_decimals, get_user_from_context, get_table, UserStatus, SegmentStatus

def validate_segment_data(data, required_fields=None):
    """Validate segment data"""
    if required_fields is None:
        required_fields = ['name']
    
    errors = []
    
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"{field} is required")
    
    # Validate name
    if 'name' in data and len(data['name']) > 100:
        errors.append("Segment name must be 100 characters or less")
    
    # Validate description
    if 'description' in data and len(data['description']) > 500:
        errors.append("Segment description must be 500 characters or less")
    
    # Validate emails list
    if 'emails' in data:
        emails = data['emails']
        if not isinstance(emails, list):
            errors.append("emails must be a list")
        elif len(emails) > 10000:
            errors.append("emails list cannot contain more than 10,000 addresses")
        else:
            import re
            email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            invalid_emails = []
            for i, email in enumerate(emails):
                if not isinstance(email, str) or not email_pattern.match(email):
                    invalid_emails.append(f"emails[{i}]: '{email}'")
                    if len(invalid_emails) >= 5:  # Limit error reporting
                        invalid_emails.append("... and more")
                        break
            if invalid_emails:
                errors.append(f"Invalid email addresses: {', '.join(invalid_emails)}")
    
    return errors

def get_all_emails_from_segments(active_only=False):
    """Get unique emails from all segments"""
    try:
        segments_table = get_table('DYNAMODB_SEGMENTS_TABLE')
        
        # Scan all segments
        response = segments_table.scan()
        segments = response.get('Items', [])
        
        # Collect all emails from all segments
        all_emails = set()
        for segment in segments:
            if active_only and segment.get('status') != SegmentStatus.ACTIVE.value:
                continue
            emails = segment.get('emails', [])
            all_emails.update(emails)
        
        return list(all_emails)
    except Exception as e:
        print(f"Error getting all emails from segments: {e}")
        return []

def count_all_emails_from_segments(active_only=False):
    """Count unique emails from all segments"""
    emails = get_all_emails_from_segments(active_only=active_only)
    return len(emails)

def count_segment_contacts(segment_id, emails_list=None):
    """Count contacts in a segment (contacts table removed - using segments only)"""
    try:
        if segment_id == 'all_active':
            # Count from all active segments
            return count_all_emails_from_segments(active_only=True)
        elif segment_id == 'all_contacts':
            # Count from all segments
            return count_all_emails_from_segments(active_only=False)
        else:
            # For custom segments, count based on emails list
            if emails_list:
                return len(emails_list)
            else:
                # Get segment and count its emails
                segments_table = get_table('DYNAMODB_SEGMENTS_TABLE')
                response = segments_table.get_item(Key={'id': segment_id})
                if 'Item' in response:
                    emails = response['Item'].get('emails', [])
                    return len(emails)
                return 0
    except Exception as e:
        print(f"Error counting contacts for segment {segment_id}: {e}")
        return 0

def create_segment(event):
    """Create a new segment"""
    user = event['user']  # User already authenticated in handler
    
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON in request body"})
    
    # Validate required fields
    errors = validate_segment_data(body, ['name'])
    if errors:
        return _response(400, {"error": "Validation failed", "details": errors})
    
    segments_table = get_table('DYNAMODB_SEGMENTS_TABLE')
    
    # Auto-generate segment ID
    segment_id = str(uuid.uuid4())
    current_time = int(time.time())
    
    # Get emails list and validate
    emails = body.get('emails', [])
    if not emails:
        return _response(400, {"error": "emails list is required and cannot be empty"})
    
    # Remove duplicates and normalize emails
    unique_emails = list(set(email.lower().strip() for email in emails))
    
    # Create segment with owner information
    segment_item = {
        'id': segment_id,
        'name': body['name'],
        'description': body.get('description', ''),
        'emails': unique_emails,
        'criteria': body.get('criteria', {}),
        'status': body.get('status', SegmentStatus.ACTIVE.value),
        'contact_count': len(unique_emails),
        'created_at': current_time,
        'updated_at': current_time,
        'created_by': user['id'],
        'owner_id': user['id'],  # Add owner information
        'tags': body.get('tags', [])
    }
    
    try:
        segments_table.put_item(Item=segment_item)
        
        return _response(201, {
            "message": "Segment created successfully",
            "segment": segment_item
        })
        
    except Exception as e:
        return _response(500, {"error": f"Failed to create segment: {str(e)}"})

def get_segment(event):
    """Get a specific segment by ID"""
    user = event['user']  # User already authenticated in handler
    segment_id = event['pathParameters']['id']
    
    segments_table = get_table('DYNAMODB_SEGMENTS_TABLE')
    
    try:
        response = segments_table.get_item(Key={'id': segment_id})
        
        if 'Item' not in response:
            return _response(404, {"error": f"Segment '{segment_id}' not found"})
        
        segment = convert_decimals(response['Item'])
        
        # Handle built-in segments (global access)
        if segment_id in ['all_active', 'all_contacts']:
            contact_count = count_segment_contacts(segment_id)
            segment['contact_count'] = contact_count
            return _response(200, {"segment": segment})
        
        # Check ownership for custom segments
        if segment.get('owner_id') != user['id']:
            return _response(403, {"error": "Access denied. You can only access your own segments."})
        
        return _response(200, {"segment": segment})
        
    except Exception as e:
        return _response(500, {"error": f"Failed to retrieve segment: {str(e)}"})

def list_segments(event):
    """List user's segments with optional filtering"""
    user = event['user']  # User already authenticated in handler
    query_params = event.get('queryStringParameters') or {}
    status_filter = query_params.get('status')
    limit = min(int(query_params.get('limit', 50)), 100)  # Max 100 items
    
    segments_table = get_table('DYNAMODB_SEGMENTS_TABLE')
    
    try:
        # Query user's segments using owner_id index
        filter_expression = Attr('owner_id').eq(user['id'])
        
        # Add status filter if provided
        if status_filter:
            filter_expression = filter_expression & Attr('status').eq(status_filter)
        
        # Build query parameters
        query_params = {
            'IndexName': 'owner_index',
            'KeyConditionExpression': Key('owner_id').eq(user['id']),
            'Limit': limit
        }
        
        # Only add FilterExpression if we have a filter
        if status_filter:
            query_params['FilterExpression'] = filter_expression
        
        response = segments_table.query(**query_params)
        
        segments = convert_decimals(response.get('Items', []))
        
        # Sort by updated_at (most recent first)
        segments.sort(key=lambda x: x.get('updated_at', 0), reverse=True)
        
        # Note: Built-in segments (all_active, all_contacts) are not user-specific
        # They would need special handling if we want to include them
        
        return _response(200, {
            "segments": segments,
            "count": len(segments),
            "has_more": 'LastEvaluatedKey' in response
        })
        
    except Exception as e:
        return _response(500, {"error": f"Failed to list segments: {str(e)}"})

def update_segment(event):
    """Update an existing segment"""
    user = event['user']  # User already authenticated in handler
    segment_id = event['pathParameters']['id']
    
    # Prevent updating built-in segments
    if segment_id in ['all_active', 'all_contacts']:
        return _response(400, {"error": f"Cannot update built-in segment '{segment_id}'"})
    
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON in request body"})
    
    # Validate data (ID is not required for updates)
    errors = validate_segment_data(body, required_fields=[])
    if errors:
        return _response(400, {"error": "Validation failed", "details": errors})
    
    segments_table = get_table('DYNAMODB_SEGMENTS_TABLE')
    
    # Check if segment exists and user owns it
    try:
        response = segments_table.get_item(Key={'id': segment_id})
        if 'Item' not in response:
            return _response(404, {"error": f"Segment '{segment_id}' not found"})
        
        segment = response['Item']
        if segment.get('owner_id') != user['id']:
            return _response(403, {"error": "Access denied. You can only update your own segments."})
            
    except Exception as e:
        return _response(500, {"error": f"Failed to check segment existence: {str(e)}"})
    
    # Build update expression
    update_expression = "SET updated_at = :updated_at"
    expression_values = {":updated_at": int(time.time())}
    
    # Add fields to update
    updateable_fields = ['name', 'description', 'criteria', 'status', 'tags']
    for field in updateable_fields:
        if field in body:
            update_expression += f", {field} = :{field}"
            expression_values[f":{field}"] = body[field]
    
    # Handle emails update separately
    if 'emails' in body:
        emails = body['emails']
        unique_emails = list(set(email.lower().strip() for email in emails))
        update_expression += ", emails = :emails, contact_count = :count"
        expression_values[":emails"] = unique_emails
        expression_values[":count"] = len(unique_emails)
    
    try:
        segments_table.update_item(
            Key={'id': segment_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues='ALL_NEW'
        )
        
        # Get updated segment
        response = segments_table.get_item(Key={'id': segment_id})
        segment = convert_decimals(response['Item'])
        
        return _response(200, {
            "message": "Segment updated successfully",
            "segment": segment
        })
        
    except Exception as e:
        return _response(500, {"error": f"Failed to update segment: {str(e)}"})

def delete_segment(event):
    """Delete a segment"""
    user = event['user']  # User already authenticated in handler
    segment_id = event['pathParameters']['id']
    
    # Prevent deletion of built-in segments
    if segment_id in ['all_active', 'all_contacts']:
        return _response(400, {"error": f"Cannot delete built-in segment '{segment_id}'"})
    
    segments_table = get_table('DYNAMODB_SEGMENTS_TABLE')
    
    # Check if segment exists and user owns it
    try:
        response = segments_table.get_item(Key={'id': segment_id})
        if 'Item' not in response:
            return _response(404, {"error": f"Segment '{segment_id}' not found"})
            
        segment = response['Item']
        if segment.get('owner_id') != user['id']:
            return _response(403, {"error": "Access denied. You can only delete your own segments."})
            
    except Exception as e:
        return _response(500, {"error": f"Failed to check segment existence: {str(e)}"})

    try:
        segments_table.delete_item(Key={'id': segment_id})
        
        # TODO: Also remove segment_id from contacts table if needed
        # This could be done as a background job for large datasets
        
        return _response(200, {"message": f"Segment '{segment_id}' deleted successfully"})
        
    except Exception as e:
        return _response(500, {"error": f"Failed to delete segment: {str(e)}"})

def get_segment_contacts(event):
    """Get emails in a segment"""
    user = event['user']  # User already authenticated in handler
    segment_id = event['pathParameters']['id']
    query_params = event.get('queryStringParameters') or {}
    limit = min(int(query_params.get('limit', 50)), 100)
    
    try:
        if segment_id == 'all_active':
            # Get emails from all active segments
            all_emails = get_all_emails_from_segments(active_only=True)
            emails = all_emails[:limit]
        elif segment_id == 'all_contacts':
            # Get emails from all segments
            all_emails = get_all_emails_from_segments(active_only=False)
            emails = all_emails[:limit]
        else:
            # Get emails from segment
            segments_table = get_table('DYNAMODB_SEGMENTS_TABLE')
            response = segments_table.get_item(Key={'id': segment_id})
            
            if 'Item' not in response:
                return _response(404, {"error": f"Segment '{segment_id}' not found"})
            
            item = convert_decimals(response['Item'])
            
            # Check ownership for custom segments
            if item.get('owner_id') != user['id']:
                return _response(403, {"error": "Access denied. You can only access your own segments."})
            
            segment_emails = item.get('emails', [])
            # Apply limit to emails list
            emails = segment_emails[:limit]
        
        return _response(200, {
            "segment_id": segment_id,
            "emails": emails,
            "count": len(emails),
            "has_more": len(emails) == limit and (segment_id not in ['all_active', 'all_contacts'] and len(segment_emails) > limit)
        })
        
    except Exception as e:
        return _response(500, {"error": f"Failed to get segment emails: {str(e)}"})

def add_emails_to_segment(event):
    """Add emails to a segment"""
    user = event['user']  # User already authenticated in handler
    segment_id = event['pathParameters']['id']
    
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON in request body"})
    
    new_emails = body.get('emails', [])
    if not new_emails:
        return _response(400, {"error": "emails list is required"})
    
    # Validate emails
    import re
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    invalid_emails = [email for email in new_emails if not email_pattern.match(email)]
    if invalid_emails:
        return _response(400, {"error": f"Invalid emails: {', '.join(invalid_emails[:5])}"})
    
    segments_table = get_table('DYNAMODB_SEGMENTS_TABLE')
    
    try:
        # Get current segment
        response = segments_table.get_item(Key={'id': segment_id})
        if 'Item' not in response:
            return _response(404, {"error": f"Segment '{segment_id}' not found"})
        
        item = convert_decimals(response['Item'])
        
        # Check ownership
        if item.get('owner_id') != user['id']:
            return _response(403, {"error": "Access denied. You can only modify your own segments."})
        
        current_emails = set(item.get('emails', []))
        new_emails_set = set(email.lower().strip() for email in new_emails)
        
        # Merge emails
        updated_emails = list(current_emails | new_emails_set)
        
        # Update segment
        segments_table.update_item(
            Key={'id': segment_id},
            UpdateExpression='SET emails = :emails, contact_count = :count, updated_at = :time',
            ExpressionAttributeValues={
                ':emails': updated_emails,
                ':count': len(updated_emails),
                ':time': int(time.time())
            }
        )
        
        added_count = len(new_emails_set - current_emails)
        
        return _response(200, {
            "message": f"Added {added_count} new emails to segment '{segment_id}'",
            "total_emails": len(updated_emails)
        })
        
    except Exception as e:
        return _response(500, {"error": f"Failed to add emails to segment: {str(e)}"})

def remove_emails_from_segment(event):
    """Remove emails from a segment"""
    user = event['user']  # User already authenticated in handler
    segment_id = event['pathParameters']['id']
    
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON in request body"})
    
    emails_to_remove = body.get('emails', [])
    if not emails_to_remove:
        return _response(400, {"error": "emails list is required"})
    
    segments_table = get_table('DYNAMODB_SEGMENTS_TABLE')
    
    try:
        # Get current segment
        response = segments_table.get_item(Key={'id': segment_id})
        if 'Item' not in response:
            return _response(404, {"error": f"Segment '{segment_id}' not found"})
        
        item = convert_decimals(response['Item'])
        
        # Check ownership
        if item.get('owner_id') != user['id']:
            return _response(403, {"error": "Access denied. You can only modify your own segments."})
        
        current_emails = set(item.get('emails', []))
        emails_to_remove_set = set(email.lower().strip() for email in emails_to_remove)
        
        # Remove emails
        updated_emails = list(current_emails - emails_to_remove_set)
        
        # Update segment
        segments_table.update_item(
            Key={'id': segment_id},
            UpdateExpression='SET emails = :emails, contact_count = :count, updated_at = :time',
            ExpressionAttributeValues={
                ':emails': updated_emails,
                ':count': len(updated_emails),
                ':time': int(time.time())
            }
        )
        
        removed_count = len(current_emails & emails_to_remove_set)
        
        return _response(200, {
            "message": f"Removed {removed_count} emails from segment '{segment_id}'",
            "total_emails": len(updated_emails)
        })
        
    except Exception as e:
        return _response(500, {"error": f"Failed to remove emails from segment: {str(e)}"})

def refresh_segment_counts(event):
    """Refresh contact counts for user's segments"""
    user = event['user']  # User already authenticated in handler
    segments_table = get_table('DYNAMODB_SEGMENTS_TABLE')
    
    try:
        # Get user's segments only
        response = segments_table.query(
            IndexName='owner_index',
            KeyConditionExpression=Key('owner_id').eq(user['id'])
        )
        segments = response.get('Items', [])
        
        updated_segments = []
        
        for segment in segments:
            segment_id = segment['id']
            contact_count = count_segment_contacts(segment_id)
            
            # Update segment with new count
            segments_table.update_item(
                Key={'id': segment_id},
                UpdateExpression='SET contact_count = :count, updated_at = :time',
                ExpressionAttributeValues={
                    ':count': contact_count,
                    ':time': int(time.time())
                }
            )
            
            updated_segments.append({
                'id': segment_id,
                'name': segment.get('name', ''),
                'contact_count': contact_count
            })
        
        return _response(200, {
            "message": f"Updated contact counts for {len(updated_segments)} segments",
            "segments": updated_segments
        })
        
    except Exception as e:
        return _response(500, {"error": f"Failed to refresh segment counts: {str(e)}"})

def lambda_handler(event, context):
    """Main handler for segments API"""
    http_method = event.get('requestContext', {}).get('http', {}).get('method') or event.get('httpMethod', 'GET')
    path = event.get('rawPath') or event.get('path', '')
    
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
        if path == '/segments' or path == '/v1/segments':
            if http_method == 'GET':
                return list_segments(event)
            elif http_method == 'POST':
                return create_segment(event)
        
        elif path.startswith('/segments/') or path.startswith('/v1/segments/'):
            # Get segment ID from path parameters or extract from path
            path_params = event.get('pathParameters', {})
            segment_id = path_params.get('id')
            
            if not segment_id:
                path_parts = path.strip('/').split('/')
                # Find segments index and get the next part as segment_id
                segments_index = next((i for i, part in enumerate(path_parts) if part == 'segments'), -1)
                if segments_index >= 0 and len(path_parts) > segments_index + 1:
                    segment_id = path_parts[segments_index + 1]
            
            if segment_id:
                # Check for sub-resources
                path_parts = path.strip('/').split('/')
                segments_index = next((i for i, part in enumerate(path_parts) if part == 'segments'), -1)
                sub_resource = None
                
                if segments_index >= 0 and len(path_parts) > segments_index + 2:
                    sub_resource = path_parts[segments_index + 2]
                
                # Ensure pathParameters exists for route handlers
                if 'pathParameters' not in event or not event['pathParameters']:
                    event['pathParameters'] = {'id': segment_id}
                
                # Handle sub-resources like /v1/segments/{id}/emails
                if sub_resource in ['emails', 'contacts']:
                    if http_method == 'GET':
                        return get_segment_contacts(event)
                    elif http_method == 'POST':
                        return add_emails_to_segment(event)
                    elif http_method == 'DELETE':
                        return remove_emails_from_segment(event)
                
                # Handle main segment operations
                else:
                    if http_method == 'GET':
                        return get_segment(event)
                    elif http_method == 'PUT':
                        return update_segment(event)
                    elif http_method == 'DELETE':
                        return delete_segment(event)
        
        elif path == '/segments/refresh-counts' or path == '/v1/segments/refresh-counts':
            if http_method == 'POST':
                return refresh_segment_counts(event)
        
        # Route not found
        return _response(404, {"error": "Route not found"})
        
    except Exception as e:
        print(f"Error in segments API handler: {str(e)}")
        return _response(500, {"error": "Internal server error"})