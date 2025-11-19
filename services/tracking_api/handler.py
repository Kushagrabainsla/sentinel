import json
import os
import time
import uuid
import base64
from urllib.parse import unquote
import boto3
from botocore.exceptions import ClientError

# DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

def get_table(table_env_var):
    """Get DynamoDB table from environment variable"""
    table_name = os.environ.get(table_env_var)
    if not table_name:
        raise RuntimeError(f"{table_env_var} environment variable not set")
    return dynamodb.Table(table_name)

def record_tracking_event(campaign_id, recipient_id, email, event_type, metadata=None):
    """Record a tracking event in the events table"""
    try:
        events_table = get_table('DYNAMODB_EVENTS_TABLE')
        
        event_record = {
            'id': str(uuid.uuid4()),
            'campaign_id': str(campaign_id),
            'recipient_id': str(recipient_id),
            'email': email,
            'type': event_type,
            'created_at': int(time.time()),
            'raw': json.dumps(metadata or {})
        }
        
        events_table.put_item(Item=event_record)
        print(f"✅ Recorded {event_type} event for campaign {campaign_id}, recipient {recipient_id}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to record tracking event: {e}")
        return False

def get_link_mapping(tracking_id):
    """Get original URL from tracking ID"""
    try:
        link_mappings_table = get_table('DYNAMODB_LINK_MAPPINGS_TABLE')
        
        response = link_mappings_table.get_item(Key={'tracking_id': tracking_id})
        
        if 'Item' in response:
            return response['Item']
        return None
        
    except Exception as e:
        print(f"❌ Failed to get link mapping: {e}")
        return None

def update_recipient_status(campaign_id, recipient_id, status):
    """Update recipient status in recipients table"""
    try:
        recipients_table = get_table('DYNAMODB_RECIPIENTS_TABLE')
        
        recipients_table.update_item(
            Key={
                'campaign_id': str(campaign_id),
                'recipient_id': str(recipient_id)
            },
            UpdateExpression='SET #s = :s, last_event_at = :t',
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': status, ':t': int(time.time())}
        )
        return True
        
    except Exception as e:
        print(f"❌ Failed to update recipient status: {e}")
        return False

def generate_1x1_pixel():
    """Generate a 1x1 transparent PNG pixel"""
    # Base64 encoded 1x1 transparent PNG
    pixel_data = base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
    )
    return pixel_data

def lambda_handler(event, context):
    print("🚀 Tracking API Handler Invoked", json.dumps(event, default=str))
    """
    Handle tracking requests:
    - GET /track/open/{campaign_id}/{recipient_id}.png - Email open tracking
    - GET /track/click/{tracking_id} - Link click tracking  
    - GET /unsubscribe/{token} - Unsubscribe tracking
    - GET /events/{campaign_id} - Retrieve tracking events for a campaign
    """
    
    # Parse the request - support both API Gateway v1.0 and v2.0 formats
    if 'version' in event and event['version'] == '2.0':
        # API Gateway v2.0 format
        http_method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
        path = event.get('rawPath', '')
        headers = event.get('headers', {})
        query_params = event.get('queryStringParameters') or {}
        path_params = event.get('pathParameters') or {}
        
        # For v2.0, the tracking ID is in pathParameters.proxy
        if 'proxy' in path_params:
            tracking_id = path_params['proxy']
        else:
            tracking_id = None
            
    else:
        # API Gateway v1.0 format (fallback)
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '')
        headers = event.get('headers', {})
        query_params = event.get('queryStringParameters') or {}
        tracking_id = None
    
    print(f"📊 Tracking request: {http_method} {path}")
    print(f"🔍 Parsed tracking_id: {tracking_id}")
    
    # Extract user agent and IP for analytics
    user_agent = headers.get('user-agent', headers.get('User-Agent', ''))
    ip_address = headers.get('x-forwarded-for', headers.get('X-Forwarded-For', '')).split(',')[0].strip() or headers.get('x-real-ip', headers.get('X-Real-IP', 'unknown'))
    
    try:
        # Route based on path
        if path.startswith('/track/open/'):
            return handle_open_tracking(path, user_agent, ip_address, query_params)
        elif path.startswith('/track/click/'):
            return handle_click_tracking(path, user_agent, ip_address, query_params, tracking_id)
        elif path.startswith('/unsubscribe/'):
            return handle_unsubscribe(path, user_agent, ip_address, query_params)
        elif path.startswith('/events/'):
            return handle_events_api(path, http_method, query_params)
        else:
            print(f"❌ Unknown tracking path: {path}")
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Not found'})
            }
            
    except Exception as e:
        print(f"❌ Tracking handler error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }

def handle_open_tracking(path, user_agent, ip_address, query_params):
    """Handle email open tracking pixel requests - redirect to S3 asset"""
    
    # Parse path: /track/open/{campaign_id}/{recipient_id}.png
    path_parts = path.strip('/').split('/')
    
    if len(path_parts) >= 4:
        campaign_id = path_parts[2]
        recipient_file = path_parts[3]  # "recipient_id.png"
        recipient_id = recipient_file.split('.')[0]  # Remove .png extension
        
        # Record open event
        metadata = {
            'user_agent': user_agent,
            'ip_address': ip_address,
            'timestamp': int(time.time()),
            'query_params': query_params
        }
        
        record_tracking_event(
            campaign_id=campaign_id,
            recipient_id=recipient_id,
            email=query_params.get('email', 'unknown'),
            event_type='open',
            metadata=metadata
        )
        
        # Update recipient status to 'opened'
        update_recipient_status(campaign_id, recipient_id, 'opened')
    
    # Serve the S3 logo directly (fetch and return the image data)
    sentinel_logo_url = os.environ.get('SENTINEL_LOGO_URL')
    
    if sentinel_logo_url:
        try:
            import urllib.request
            
            # Fetch the actual logo from S3 and serve it directly
            with urllib.request.urlopen(sentinel_logo_url) as response:
                logo_data = response.read()
                
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'image/png',
                    'Cache-Control': 'public, max-age=3600',
                    'Content-Length': str(len(logo_data))
                },
                'body': base64.b64encode(logo_data).decode('utf-8'),
                'isBase64Encoded': True
            }
        except Exception as e:
            print(f"❌ Failed to fetch logo from S3: {e}")
            # Fallback to pixel
    
    # Fallback: return 1x1 transparent pixel if S3 fetch fails
    pixel_data = generate_1x1_pixel()
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'image/png',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        },
        'body': base64.b64encode(pixel_data).decode('utf-8'),
        'isBase64Encoded': True
    }

def handle_click_tracking(path, user_agent, ip_address, query_params, tracking_id=None):
    """Handle link click tracking and redirect"""
    
    # Use tracking_id from path parameters if available (API Gateway v2.0)
    # Otherwise parse from path (API Gateway v1.0 fallback)
    if not tracking_id:
        path_parts = path.strip('/').split('/')
        if len(path_parts) >= 3:
            tracking_id = path_parts[2]
    
    print(f"🔗 Processing click tracking for ID: {tracking_id}")
    
    if tracking_id:
        # Get link mapping
        link_mapping = get_link_mapping(tracking_id)
        
        if link_mapping:
            campaign_id = link_mapping['campaign_id']
            recipient_id = link_mapping['recipient_id']
            original_url = link_mapping['original_url']
            link_id = link_mapping.get('link_id', 'unknown')
            
            print(f"✅ Found mapping: {original_url} for campaign {campaign_id}")
            
            # Record click event
            metadata = {
                'user_agent': user_agent,
                'ip_address': ip_address,
                'timestamp': int(time.time()),
                'link_id': link_id,
                'original_url': original_url,
                'tracking_id': tracking_id,
                'query_params': query_params
            }
            
            record_tracking_event(
                campaign_id=campaign_id,
                recipient_id=recipient_id,
                email=link_mapping.get('email', 'unknown'),
                event_type='click',
                metadata=metadata
            )
            
            # Update recipient status to 'clicked'
            update_recipient_status(campaign_id, recipient_id, 'clicked')
            
            # Redirect to original URL
            return {
                'statusCode': 302,
                'headers': {
                    'Location': original_url,
                    'Cache-Control': 'no-cache'
                },
                'body': ''
            }
        else:
            # Tracking ID not found in database
            print(f"⚠️ Tracking ID not found in database: {tracking_id}")
    else:
        print(f"❌ No tracking ID found in request")
    
    # If tracking ID not found or path format is wrong, redirect to fallback URL
    fallback_url = query_params.get('fallback', 'https://thesentinel.site')
    
    print(f"🔄 Redirecting to fallback URL: {fallback_url}")
    
    return {
        'statusCode': 302,
        'headers': {
            'Location': fallback_url
        },
        'body': ''
    }

def handle_unsubscribe(path, user_agent, ip_address, query_params):
    """Handle unsubscribe tracking"""
    
    # Parse path: /unsubscribe/{token}
    path_parts = path.strip('/').split('/')
    
    if len(path_parts) >= 2:
        token = path_parts[1]
        
        # TODO: Implement token validation and unsubscribe logic
        # For now, return a simple unsubscribe page
        
        # Record unsubscribe event (you'd decode token to get campaign/recipient info)
        metadata = {
            'user_agent': user_agent,
            'ip_address': ip_address,
            'timestamp': int(time.time()),
            'token': token
        }
        
        # Note: In production, decode token to get actual campaign_id and recipient_id
        print(f"📋 Unsubscribe request with token: {token}")
    
    # Return unsubscribe confirmation page
    unsubscribe_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Unsubscribe - Sentinel</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            .container { max-width: 500px; margin: 0 auto; }
            .success { color: #28a745; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Unsubscribe Successful</h1>
            <p class="success">✅ You have been successfully unsubscribed from our mailing list.</p>
            <p>You will no longer receive emails from this campaign.</p>
            <p><a href="https://thesentinel.site">Return to Sentinel</a></p>
        </div>
    </body>
    </html>
    """
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/html'
        },
        'body': unsubscribe_html
    }

def handle_events_api(path, http_method, query_params):
    """Handle events API requests - GET /events/{campaign_id}"""
    
    if http_method != 'GET':
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    # Parse path: /events/{campaign_id}
    path_parts = path.strip('/').split('/')
    
    if len(path_parts) < 2:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Campaign ID required'})
        }
    
    campaign_id = path_parts[1]
    
    try:
        events_table = get_table('DYNAMODB_EVENTS_TABLE')
        
        # Scan for events with this campaign_id
        response = events_table.scan(
            FilterExpression='campaign_id = :cid',
            ExpressionAttributeValues={':cid': campaign_id}
        )
        
        events = response.get('Items', [])
        
        # Sort events by created_at (most recent first)
        events.sort(key=lambda x: x.get('created_at', 0), reverse=True)
        
        # Group events by type for summary
        event_summary = {}
        for event in events:
            event_type = event.get('type', 'unknown')
            if event_type not in event_summary:
                event_summary[event_type] = 0
            event_summary[event_type] += 1
        
        # Format response
        result = {
            'campaign_id': campaign_id,
            'total_events': len(events),
            'event_summary': event_summary,
            'events': events[:50]  # Limit to first 50 events for performance
        }
        
        if len(events) > 50:
            result['note'] = f'Showing first 50 of {len(events)} total events'
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result, indent=2)
        }
        
    except Exception as e:
        print(f"❌ Error retrieving events for campaign {campaign_id}: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': f'Failed to retrieve events: {str(e)}'})
        }