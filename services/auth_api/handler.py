#!/usr/bin/env python3
"""
User authentication and management service for Sentinel.
Handles user registration, API key generation, and authentication.
"""

import json
import os
import time
import uuid
import hashlib
import hmac
import secrets
import re
import urllib.request
import urllib.parse
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

# Email validation pattern
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Import common utilities and enums
from common import _response, convert_decimals, get_users_table, UserStatus

def generate_api_key():
    """Generate a secure API key"""
    return f"sk_{secrets.token_urlsafe(32)}"

def hash_password(password):
    """Hash password using SHA-256 with salt"""
    salt = secrets.token_hex(32)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"

def verify_password(password, stored_hash):
    """Verify password against stored hash"""
    try:
        salt, password_hash = stored_hash.split(':')
        calculated_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return hmac.compare_digest(calculated_hash, password_hash)
    except (ValueError, AttributeError):
        return False

def get_api_key_from_event(event):
    """Extract API key from headers (handles case-sensitivity)"""
    headers = event.get('headers', {})
    if not headers:
        return None
    return headers.get('X-API-Key') or headers.get('x-api-key')

def create_user(event):
    """Create a new user"""
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON in request body"})
    
    # Validate required fields
    email = body.get('email', '').lower().strip()
    password = body.get('password', '')
    name = body.get('name', '').strip()
    
    if not email or not password or not name:
        return _response(400, {"error": "email, password, and name are required"})
    
    # Validate email format
    if not EMAIL_PATTERN.match(email):
        return _response(400, {"error": "Invalid email format"})
    
    if len(password) < 8:
        return _response(400, {"error": "Password must be at least 8 characters"})
    
    users_table = get_users_table()
    
    # Check if user already exists
    try:
        response = users_table.query(
            IndexName='email_index',
            KeyConditionExpression=Key('email').eq(email)
        )
        if response['Items']:
            return _response(409, {"error": "User with this email already exists"})
    except Exception as e:
        return _response(500, {"error": f"Failed to check existing user: {str(e)}"})
    
    # Create user
    user_id = str(uuid.uuid4())
    api_key = generate_api_key()
    password_hash = hash_password(password)
    current_time = int(time.time())
    
    user_item = {
        'id': user_id,
        'email': email,
        'name': name,
        'password_hash': password_hash,
        'api_key': api_key,
        'status': UserStatus.ACTIVE.value,
        'created_at': current_time,
        'updated_at': current_time,
        'last_login': None,
        'timezone': 'UTC'
    }
    
    try:
        users_table.put_item(Item=user_item)
        
        # Return user info without sensitive data
        user_response = convert_decimals({
            'id': user_id,
            'email': email,
            'name': name,
            'api_key': api_key,  # Only return API key on registration
            'status': UserStatus.ACTIVE.value,
            'created_at': current_time
        })
        
        return _response(201, {
            "message": "User created successfully",
            "user": user_response
        })
        
    except Exception as e:
        return _response(500, {"error": f"Failed to create user: {str(e)}"})

def authenticate_user(event):
    """Authenticate user with email/password and return API key"""
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON in request body"})
    
    email = body.get('email', '').lower().strip()
    password = body.get('password', '')
    
    if not email or not password:
        return _response(400, {"error": "email and password are required"})
    
    users_table = get_users_table()
    
    try:
        # Find user by email
        response = users_table.query(
            IndexName='email_index',
            KeyConditionExpression=Key('email').eq(email)
        )
        
        if not response['Items']:
            return _response(401, {"error": "Invalid email or password"})
        
        user = response['Items'][0]
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            return _response(401, {"error": "Invalid email or password"})
        
        if user.get('status') != UserStatus.ACTIVE.value:
            return _response(401, {"error": "User account is not active"})
        
        # Update last login
        users_table.update_item(
            Key={'id': user['id']},
            UpdateExpression='SET last_login = :time',
            ExpressionAttributeValues={':time': int(time.time())}
        )
        
        user_response = convert_decimals({
            'id': user['id'],
            'email': user['email'],
            'name': user['name'],
            'api_key': user['api_key'],
            'status': user['status']
        })
        
        return _response(200, {
            "message": "Authentication successful",
            "user": user_response
        })
        
    except Exception as e:
        return _response(500, {"error": f"Authentication failed: {str(e)}"})

def get_user_by_api_key(api_key):
    """Get user by API key - used for request authentication"""
    if not api_key:
        return None
    
    users_table = get_users_table()
    
    try:
        response = users_table.query(
            IndexName='api_key_index',
            KeyConditionExpression=Key('api_key').eq(api_key)
        )
        
        if not response['Items']:
            return None
        
        user = convert_decimals(response['Items'][0])
        
        if user.get('status') != UserStatus.ACTIVE.value:
            return None
        
        # Remove sensitive data
        user.pop('password_hash', None)
        return user
        
    except Exception as e:
        print(f"Error getting user by API key: {e}")
        return None

def get_current_user(event):
    """Get current user info from API key"""
    api_key = get_api_key_from_event(event)
    
    if not api_key:
        return _response(401, {"error": "API key required in X-API-Key header"})
    
    user = get_user_by_api_key(api_key)
    if not user:
        return _response(401, {"error": "Invalid API key"})
    
    return _response(200, {"user": user})

def update_user(event):
    """Update user profile details (name, timezone)"""
    api_key = get_api_key_from_event(event)
    if not api_key:
        return _response(401, {"error": "API key required in X-API-Key header"})
    user = get_user_by_api_key(api_key)
    if not user:
        return _response(401, {"error": "Invalid API key"})
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON in request body"})
    
    name = body.get('name', user['name'])
    timezone = body.get('timezone', user.get('timezone', 'UTC'))
    # Optionally, validate timezone string here

    users_table = get_users_table()
    users_table.update_item(
        Key={'id': user['id']},
        UpdateExpression='SET #n = :name, #tz = :tz, updated_at = :time',
        ExpressionAttributeNames={'#n': 'name', '#tz': 'timezone'},
        ExpressionAttributeValues={
            ':name': name,
            ':tz': timezone,
            ':time': int(time.time())
        }
    )
    # Return updated user info
    user['name'] = name
    user['timezone'] = timezone
    user['updated_at'] = int(time.time())
    return _response(200, {"message": "User updated successfully", "user": user})

def regenerate_api_key(event):
    """Regenerate API key for authenticated user"""
    api_key = get_api_key_from_event(event)
    
    if not api_key:
        return _response(401, {"error": "API key required in X-API-Key header"})
    
    user = get_user_by_api_key(api_key)
    if not user:
        return _response(401, {"error": "Invalid API key"})
    
    users_table = get_users_table()
    new_api_key = generate_api_key()
    
    try:
        users_table.update_item(
            Key={'id': user['id']},
            UpdateExpression='SET api_key = :key, updated_at = :time',
            ExpressionAttributeValues={
                ':key': new_api_key,
                ':time': int(time.time())
            }
        )
        
        return _response(200, {
            "message": "API key regenerated successfully",
            "api_key": new_api_key
        })
        
    except Exception as e:
        return _response(500, {"error": f"Failed to regenerate API key: {str(e)}"})

def get_google_creds():
    """Fetch Google credentials directly from Secrets Manager"""
    try:
        client = boto3.client('secretsmanager', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        response = client.get_secret_value(SecretId='sentinel_config')
        return json.loads(response['SecretString'])
    except Exception as e:
        print(f"Error fetching sentinel_config: {e}")
        return {}

def get_google_auth_url(event):
    """Generate Google OAuth authorization URL"""
    creds = get_google_creds()
    client_id = creds.get('GOOGLE_CLIENT_ID')
    redirect_uri = creds.get('GOOGLE_REDIRECT_URI')
    
    if not client_id or not redirect_uri:
        return _response(500, {"error": "Google OAuth configuration missing"})
    
    scopes = [
        'openid',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/gmail.send'
    ]
    
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        "response_type=code&"
        f"scope={' '.join(scopes)}&"
        "access_type=offline&"
        "prompt=consent"
    )
    
    return _response(200, {"url": auth_url})

def google_callback(event):
    """Handle Google OAuth callback and exchange code for tokens"""
    api_key = get_api_key_from_event(event)
    user = get_user_by_api_key(api_key)
    if not user:
        return _response(401, {"error": "Invalid API key"})
    
    try:
        body = json.loads(event.get('body', '{}'))
        code = body.get('code')
        if not code:
            return _response(400, {"error": "Authorization code is required"})
            
        creds = get_google_creds()
        client_id = creds.get('GOOGLE_CLIENT_ID')
        client_secret = creds.get('GOOGLE_CLIENT_SECRET')
        redirect_uri = creds.get('GOOGLE_REDIRECT_URI')
        
        # Exchange code for tokens
        token_data = urllib.parse.urlencode({
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }).encode()
        
        token_req = urllib.request.Request("https://oauth2.googleapis.com/token", data=token_data)
        try:
            with urllib.request.urlopen(token_req) as response:
                tokens = json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            return _response(e.code, {"error": "Failed to exchange code for tokens", "details": e.read().decode()})
            
        access_token = tokens.get('access_token')
        refresh_token = tokens.get('refresh_token')
        expires_in = tokens.get('expires_in')
        
        # Get user info from Google
        user_info_req = urllib.request.Request(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        with urllib.request.urlopen(user_info_req) as user_info_response:
            google_user = json.loads(user_info_response.read().decode())
        google_email = google_user.get('email')
        
        # Update user in DynamoDB
        users_table = get_users_table()
        update_expr = 'SET google_connected = :conn, google_email = :email, google_access_token = :at, google_token_expiry = :exp'
        attr_vals = {
            ':conn': True,
            ':email': google_email,
            ':at': access_token,
            ':exp': int(time.time()) + expires_in
        }
        
        if refresh_token:
            update_expr += ', google_refresh_token = :rt'
            attr_vals[':rt'] = refresh_token
            
        users_table.update_item(
            Key={'id': user['id']},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=attr_vals
        )
        
        return _response(200, {"message": "Google account connected successfully"})
        
    except Exception as e:
        print(f"Error in google_callback: {e}")
        return _response(500, {"error": str(e)})

def toggle_gmail(event):
    """Toggle Gmail sending for the user"""
    api_key = get_api_key_from_event(event)
    user = get_user_by_api_key(api_key)
    if not user:
        return _response(401, {"error": "Invalid API key"})
        
    try:
        body = json.loads(event.get('body', '{}'))
        enabled = body.get('enabled', False)
        
        if enabled and not user.get('google_connected'):
            return _response(400, {"error": "Connect Google account first"})
            
        users_table = get_users_table()
        users_table.update_item(
            Key={'id': user['id']},
            UpdateExpression='SET gmail_enabled = :val',
            ExpressionAttributeValues={':val': enabled}
        )
        
        user['gmail_enabled'] = enabled
        return _response(200, {"message": "Gmail status updated", "user": user})
        
    except Exception as e:
        return _response(500, {"error": str(e)})

def disconnect_google(event):
    """Disconnect Google account"""
    api_key = get_api_key_from_event(event)
    user = get_user_by_api_key(api_key)
    if not user:
        return _response(401, {"error": "Invalid API key"})
        
    try:
        users_table = get_users_table()
        users_table.update_item(
            Key={'id': user['id']},
            UpdateExpression='REMOVE google_connected, google_email, google_access_token, google_refresh_token, google_token_expiry, gmail_enabled'
        )
        
        # Remove fields from user object for response
        for field in ['google_connected', 'google_email', 'google_access_token', 'google_refresh_token', 'google_token_expiry', 'gmail_enabled']:
            user.pop(field, None)
            
        user['google_connected'] = False
        user['gmail_enabled'] = False
        
        return _response(200, {"message": "Google account disconnected", "user": user})
    except Exception as e:
        return _response(500, {"error": str(e)})

def lambda_handler(event, context):
    """Main handler for user authentication API"""
    print(f"Auth API Handler: {json.dumps(event, default=str)}")
    
    http_method = event.get('requestContext', {}).get('http', {}).get('method') or event.get('httpMethod', 'GET')
    path = event.get('rawPath') or event.get('path', '')
    
    print(f"DEBUG - HTTP Method: {http_method}")
    print(f"DEBUG - Path: {path}")
    
    # Handle CORS preflight
    if http_method == 'OPTIONS':
        return _response(200, {})
    
    try:
        # Route requests based on path and method
        if path == '/auth/register' or path == '/v1/auth/register':
            if http_method == 'POST':
                return create_user(event)
        
        elif path == '/auth/login' or path == '/v1/auth/login':
            if http_method == 'POST':
                return authenticate_user(event)
        
        elif path == '/auth/me' or path == '/v1/auth/me':
            if http_method == 'GET':
                return get_current_user(event)
            
        elif path == '/auth/update' or path == '/v1/auth/update':
            if http_method == 'POST':
                return update_user(event)
        
        elif path == '/auth/regenerate-key' or path == '/v1/auth/regenerate-key':
            if http_method == 'POST':
                return regenerate_api_key(event)
        
        elif path == '/auth/google/url' or path == '/v1/auth/google/url':
            return get_google_auth_url(event)
            
        elif path == '/auth/google/callback' or path == '/v1/auth/google/callback':
            if http_method == 'POST':
                return google_callback(event)
                
        elif path == '/auth/google/toggle-gmail' or path == '/v1/auth/google/toggle-gmail':
            if http_method == 'POST':
                return toggle_gmail(event)
                
        elif path == '/auth/google/disconnect' or path == '/v1/auth/google/disconnect':
            if http_method == 'POST':
                return disconnect_google(event)
        
        # Route not found
        return _response(404, {"error": "Route not found"})
        
    except Exception as e:
        print(f"Error in auth API handler: {e}")
        return _response(500, {"error": "Internal server error"})