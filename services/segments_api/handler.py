import json
import os
import time
import uuid
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

# DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

def get_table(table_env_var):
    """Get DynamoDB table from environment variable"""
    table_name = os.environ.get(table_env_var)
    if not table_name:
        raise RuntimeError(f"{table_env_var} environment variable not set")
    return dynamodb.Table(table_name)

def _response(status_code, body, headers=None):
    """Helper function to create API Gateway response"""
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": json.dumps(body)
    }

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
            if active_only and segment.get('status') != 'active':
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
    
    # Create segment
    segment_item = {
        'id': segment_id,
        'name': body['name'],
        'description': body.get('description', ''),
        'emails': unique_emails,
        'criteria': body.get('criteria', {}),
        'status': body.get('status', 'active'),
        'contact_count': len(unique_emails),
        'created_at': current_time,
        'updated_at': current_time,
        'created_by': body.get('created_by', 'api'),
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
    segment_id = event['pathParameters']['id']
    
    segments_table = get_table('DYNAMODB_SEGMENTS_TABLE')
    
    try:
        response = segments_table.get_item(Key={'id': segment_id})
        
        if 'Item' not in response:
            return _response(404, {"error": f"Segment '{segment_id}' not found"})
        
        segment = response['Item']
        
        # Update contact count in real-time for built-in segments
        if segment_id in ['all_active', 'all_contacts']:
            contact_count = count_segment_contacts(segment_id)
            segment['contact_count'] = contact_count
        
        return _response(200, {"segment": segment})
        
    except Exception as e:
        return _response(500, {"error": f"Failed to retrieve segment: {str(e)}"})

def list_segments(event):
    """List all segments with optional filtering"""
    query_params = event.get('queryStringParameters') or {}
    status_filter = query_params.get('status')
    limit = min(int(query_params.get('limit', 50)), 100)  # Max 100 items
    
    segments_table = get_table('DYNAMODB_SEGMENTS_TABLE')
    
    try:
        if status_filter:
            response = segments_table.scan(
                FilterExpression=Attr('status').eq(status_filter),
                Limit=limit
            )
        else:
            response = segments_table.scan(Limit=limit)
        
        segments = response.get('Items', [])
        
        # Sort by updated_at (most recent first)
        segments.sort(key=lambda x: x.get('updated_at', 0), reverse=True)
        
        # Add real-time contact counts for built-in segments
        for segment in segments:
            if segment['id'] in ['all_active', 'all_contacts']:
                segment['contact_count'] = count_segment_contacts(segment['id'])
        
        return _response(200, {
            "segments": segments,
            "count": len(segments),
            "has_more": 'LastEvaluatedKey' in response
        })
        
    except Exception as e:
        return _response(500, {"error": f"Failed to list segments: {str(e)}"})

def update_segment(event):
    """Update an existing segment"""
    segment_id = event['pathParameters']['id']
    
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON in request body"})
    
    # Validate data (ID is not required for updates)
    errors = validate_segment_data(body, required_fields=[])
    if errors:
        return _response(400, {"error": "Validation failed", "details": errors})
    
    segments_table = get_table('DYNAMODB_SEGMENTS_TABLE')
    
    # Check if segment exists
    try:
        response = segments_table.get_item(Key={'id': segment_id})
        if 'Item' not in response:
            return _response(404, {"error": f"Segment '{segment_id}' not found"})
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
        segment = response['Item']
        
        return _response(200, {
            "message": "Segment updated successfully",
            "segment": segment
        })
        
    except Exception as e:
        return _response(500, {"error": f"Failed to update segment: {str(e)}"})

def delete_segment(event):
    """Delete a segment"""
    segment_id = event['pathParameters']['id']
    
    # Prevent deletion of built-in segments
    if segment_id in ['all_active', 'all_contacts']:
        return _response(400, {"error": f"Cannot delete built-in segment '{segment_id}'"})
    
    segments_table = get_table('DYNAMODB_SEGMENTS_TABLE')
    
    # Check if segment exists
    try:
        response = segments_table.get_item(Key={'id': segment_id})
        if 'Item' not in response:
            return _response(404, {"error": f"Segment '{segment_id}' not found"})
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
            
            segment_emails = response['Item'].get('emails', [])
            # Apply limit to emails list
            emails = segment_emails[:limit]
        
        return _response(200, {
            "segment_id": segment_id,
            "emails": emails,
            "count": len(emails),
            "has_more": len(emails) == limit and (segment_id not in ['all_active', 'all_contacts'] and len(response['Item'].get('emails', [])) > limit)
        })
        
    except Exception as e:
        return _response(500, {"error": f"Failed to get segment emails: {str(e)}"})

def add_emails_to_segment(event):
    """Add emails to a segment"""
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
        
        current_emails = set(response['Item'].get('emails', []))
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
        
        current_emails = set(response['Item'].get('emails', []))
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
    """Refresh contact counts for all segments"""
    segments_table = get_table('DYNAMODB_SEGMENTS_TABLE')
    
    try:
        # Get all segments
        response = segments_table.scan()
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
    print(f"Segments API Handler - Full Event: {json.dumps(event, default=str)}")
    
    http_method = event.get('requestContext', {}).get('http', {}).get('method') or event.get('httpMethod', 'GET')
    path = event.get('rawPath') or event.get('path', '')
    
    print(f"DEBUG - HTTP Method: {http_method}")
    print(f"DEBUG - Path: {path}")
    print(f"DEBUG - Path Parameters: {event.get('pathParameters')}")
    print(f"DEBUG - Query Parameters: {event.get('queryStringParameters')}")
    print(f"DEBUG - Request Context: {event.get('requestContext', {})}")
    
    # Handle CORS preflight
    if http_method == 'OPTIONS':
        return _response(200, {})
    
    try:
        # Route requests based on path and method
        if path == '/segments' or path == '/v1/segments':
            if http_method == 'GET':
                return list_segments(event)
            elif http_method == 'POST':
                return create_segment(event)
        
        elif path.startswith('/segments/') or path.startswith('/v1/segments/'):
            # First check if API Gateway v2 already provided pathParameters
            path_params = event.get('pathParameters', {})
            segment_id = path_params.get('id') if path_params else None
            
            # If not provided, extract segment ID from path manually
            if not segment_id:
                path_parts = path.strip('/').split('/')
                print(f"DEBUG - Path parts: {path_parts}")
                
                # For /v1/segments/{id}, path_parts = ['v1', 'segments', 'id']
                # For /segments/{id}, path_parts = ['segments', 'id'] 
                segments_index = -1
                for i, part in enumerate(path_parts):
                    if part == 'segments':
                        segments_index = i
                        break
                
                if segments_index >= 0 and len(path_parts) > segments_index + 1:
                    segment_id = path_parts[segments_index + 1]
                    print(f"DEBUG - Extracted segment_id: {segment_id}")
            
            if segment_id:
                # Check for sub-resources
                path_parts = path.strip('/').split('/')
                is_sub_resource = False
                sub_resource = None
                
                # Find segments index and check if there's a sub-resource after the ID
                segments_index = -1
                for i, part in enumerate(path_parts):
                    if part == 'segments':
                        segments_index = i
                        break
                
                if segments_index >= 0 and len(path_parts) > segments_index + 2:
                    sub_resource = path_parts[segments_index + 2]
                    is_sub_resource = True
                
                # Create modified event with proper pathParameters
                modified_event = event.copy()
                modified_event['pathParameters'] = {'id': segment_id}
                
                # Handle sub-resources like /v1/segments/{id}/emails
                if is_sub_resource and sub_resource in ['emails', 'contacts']:
                    if http_method == 'GET':
                        return get_segment_contacts(modified_event)
                    elif http_method == 'POST':
                        return add_emails_to_segment(modified_event)
                    elif http_method == 'DELETE':
                        return remove_emails_from_segment(modified_event)
                
                # Handle main segment operations
                else:
                    if http_method == 'GET':
                        return get_segment(modified_event)
                    elif http_method == 'PUT':
                        return update_segment(modified_event)
                    elif http_method == 'DELETE':
                        return delete_segment(modified_event)
        
        elif path == '/segments/refresh-counts' or path == '/v1/segments/refresh-counts':
            if http_method == 'POST':
                return refresh_segment_counts(event)
        
        # Route not found
        return _response(404, {"error": "Route not found"})
        
    except Exception as e:
        print(f"Error in segments API handler: {e}")
        return _response(500, {"error": "Internal server error"})