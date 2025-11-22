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
import secrets
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

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
        return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
    except ValueError:
        return False

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
    import re
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    if not email_pattern.match(email):
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
    api_key = event.get('headers', {}).get('X-API-Key') or event.get('headers', {}).get('x-api-key')
    
    if not api_key:
        return _response(401, {"error": "API key required in X-API-Key header"})
    
    user = get_user_by_api_key(api_key)
    if not user:
        return _response(401, {"error": "Invalid API key"})
    
    return _response(200, {"user": user})

def update_user(event):
    """Update user profile details (name, timezone)"""
    api_key = event.get('headers', {}).get('X-API-Key') or event.get('headers', {}).get('x-api-key')
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
    api_key = event.get('headers', {}).get('X-API-Key') or event.get('headers', {}).get('x-api-key')
    
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
        
        # Route not found
        return _response(404, {"error": "Route not found"})
        
    except Exception as e:
        print(f"Error in auth API handler: {e}")
        return _response(500, {"error": "Internal server error"})