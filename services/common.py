#!/usr/bin/env python3
"""
Common utilities and enums for Sentinel services

This module contains all shared utility functions and enum definitions used across
different services in the Sentinel email marketing platform.
Consolidated into a single file for simplified deployment.
"""

import json
import os
import re
from decimal import Decimal
from enum import Enum
import boto3
import requests
from botocore.exceptions import ClientError

# ================================
# USER AND AUTHENTICATION ENUMS
# ================================

class UserStatus(Enum):
    """User account status"""
    ACTIVE = "A"      # Active user account
    INACTIVE = "I"    # Inactive user account
    SUSPENDED = "S"   # Suspended user account
    DELETED = "D"     # Soft-deleted user account

# ================================
# CAMPAIGN ENUMS
# ================================

class CampaignType(Enum):
    """Campaign execution timing types"""
    IMMEDIATE = "I"  # Immediate execution
    SCHEDULED = "S"  # Scheduled execution

class CampaignDeliveryType(Enum):
    """Campaign delivery mechanism types"""
    INDIVIDUAL = "IND"   # Single recipient
    SEGMENT = "SEG"      # Segment-based (multiple recipients)

class CampaignState(Enum):
    """Campaign execution states"""
    SCHEDULED = "SC"  # Scheduled for future execution
    PENDING = "P"     # Pending immediate execution
    SENDING = "SE"    # Currently sending
    DONE = "D"        # Completed
    FAILED = "F"      # Failed

class CampaignStatus(Enum):
    """Campaign lifecycle status"""
    ACTIVE = "A"      # Active campaign
    INACTIVE = "I"    # Inactive campaign
    DELETED = "D"     # Soft-deleted campaign

# ================================
# SEGMENT ENUMS
# ================================

class SegmentStatus(Enum):
    """Segment lifecycle status"""
    ACTIVE = "A"      # Active segment
    INACTIVE = "I"    # Inactive segment
    DELETED = "D"     # Soft-deleted segment

class SegmentType(Enum):
    """Segment creation types"""
    MANUAL = "M"      # Manually created segment
    DYNAMIC = "D"     # Dynamically generated segment
    TEMPORARY = "T"   # Temporary segment (auto-created for campaigns)

# ================================
# EMAIL TRACKING ENUMS
# ================================

class EventType(Enum):
    """Email tracking event types"""
    DELIVERED = "delivered"
    OPEN = "open"
    CLICK = "click"
    BOUNCE = "bounce"
    UNSUBSCRIBE = "unsubscribe"
    SPAM = "spam"
    UNKNOWN = "unknown"

class DeliveryStatus(Enum):
    """Email delivery status"""
    SENT = "sent"
    FAILED = "failed"
    QUEUED = "queued"
    PROCESSING = "processing"

# ================================
# USER AGENT ANALYSIS ENUMS
# ================================

class OperatingSystem(Enum):
    """Operating system types for user agent analysis"""
    IOS = "iOS"
    ANDROID = "Android"
    WINDOWS_10 = "Windows 10"
    WINDOWS_8_1 = "Windows 8.1"
    WINDOWS_8 = "Windows 8"
    WINDOWS_7 = "Windows 7"
    WINDOWS = "Windows"
    MACOS = "macOS"
    LINUX = "Linux"
    UBUNTU = "Ubuntu"
    UNKNOWN = "Unknown"

class DeviceType(Enum):
    """Device types for user agent analysis"""
    IPHONE = "iPhone"
    IPAD = "iPad"
    ANDROID_PHONE = "Android Phone"
    ANDROID_TABLET = "Android Tablet"
    DESKTOP = "Desktop"
    UNKNOWN = "Unknown"

class Browser(Enum):
    """Browser types for user agent analysis"""
    MICROSOFT_EDGE = "Microsoft Edge"
    OPERA = "Opera"
    FIREFOX = "Firefox"
    SAFARI = "Safari"
    CHROME = "Chrome"
    INTERNET_EXPLORER = "Internet Explorer"
    UNKNOWN = "Unknown"

# ================================
# ENGAGEMENT ENUMS
# ================================

class EngagementLevel(Enum):
    """Recipient engagement levels"""
    HIGHLY_ENGAGED = "highly_engaged"
    MODERATELY_ENGAGED = "moderately_engaged"
    LOW_ENGAGED = "low_engaged"

# ================================
# ENUM UTILITY FUNCTIONS
# ================================

def get_all_enum_values():
    """Get a summary of all available enum values for API documentation"""
    return {
        "user_statuses": [e.value for e in UserStatus],
        "campaign_types": [e.value for e in CampaignType],
        "campaign_delivery_types": [e.value for e in CampaignDeliveryType], 
        "campaign_states": [e.value for e in CampaignState],
        "campaign_statuses": [e.value for e in CampaignStatus],
        "segment_statuses": [e.value for e in SegmentStatus],
        "segment_types": [e.value for e in SegmentType],
        "event_types": [e.value for e in EventType],
        "delivery_statuses": [e.value for e in DeliveryStatus],
        "operating_systems": [e.value for e in OperatingSystem],
        "device_types": [e.value for e in DeviceType],
        "browsers": [e.value for e in Browser],
        "engagement_levels": [e.value for e in EngagementLevel]
    }

# Validation functions for common enum types
def validate_user_status(status):
    """Validate user status against enum values"""
    return status in [e.value for e in UserStatus]

def validate_campaign_type(campaign_type):
    """Validate campaign type against enum values"""
    return campaign_type in [e.value for e in CampaignType]

def validate_event_type(event_type):
    """Validate event type against enum values"""
    return event_type in [e.value for e in EventType]

def validate_segment_status(status):
    """Validate segment status against enum values"""
    return status in [e.value for e in SegmentStatus]

# ================================
# DYNAMODB UTILITIES
# ================================

# DynamoDB resource (lazy initialization)
_dynamodb = None

def get_dynamodb():
    """Get shared DynamoDB resource with lazy initialization"""
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    return _dynamodb

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

def decimal_to_int(obj):
    """Convert DynamoDB Decimal objects to regular Python types for JSON serialization"""
    if isinstance(obj, dict):
        return {key: decimal_to_int(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_int(item) for item in obj]
    elif isinstance(obj, Decimal):
        # Convert Decimal to int if it's a whole number, otherwise float
        return int(obj) if obj % 1 == 0 else float(obj)
    else:
        return obj

def get_table(table_env_var):
    """Get DynamoDB table from environment variable"""
    table_name = os.environ.get(table_env_var)
    if not table_name:
        raise RuntimeError(f"{table_env_var} environment variable not set")
    return get_dynamodb().Table(table_name)

# Database table getters for common tables
def get_users_table():
    """Get users table"""
    return get_table('DYNAMODB_USERS_TABLE')

def get_campaigns_table():
    """Get campaigns table"""
    return get_table('DYNAMODB_CAMPAIGNS_TABLE')

def get_segments_table():
    """Get segments table"""
    return get_table('DYNAMODB_SEGMENTS_TABLE')

def get_events_table():
    """Get events table"""
    return get_table('DYNAMODB_EVENTS_TABLE')

def get_link_mappings_table():
    """Get link mappings table"""
    return get_table('DYNAMODB_LINK_MAPPINGS_TABLE')

# ================================
# API UTILITIES
# ================================

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

# ================================
# USER AGENT PARSING
# ================================

def parse_user_agent(user_agent):
    """Parse user agent string to extract browser, OS, and device information"""
    if not user_agent:
        return {
            'browser': 'Unknown',
            'browser_version': 'Unknown',
            'os': 'Unknown',
            'os_version': 'Unknown',
            'device_type': 'Unknown',
            'is_mobile': False,
            'is_tablet': False,
            'is_desktop': True
        }
    
    user_agent = user_agent.lower()
    
    # Browser detection
    browser = 'Unknown'
    browser_version = 'Unknown'
    
    if 'chrome' in user_agent and 'edge' not in user_agent:
        browser = 'Chrome'
        match = re.search(r'chrome/([\d\.]+)', user_agent)
        if match:
            browser_version = match.group(1)
    elif 'firefox' in user_agent:
        browser = 'Firefox'
        match = re.search(r'firefox/([\d\.]+)', user_agent)
        if match:
            browser_version = match.group(1)
    elif 'safari' in user_agent and 'chrome' not in user_agent:
        browser = 'Safari'
        match = re.search(r'version/([\d\.]+)', user_agent)
        if match:
            browser_version = match.group(1)
    elif 'edge' in user_agent:
        browser = 'Edge'
        match = re.search(r'edge/([\d\.]+)', user_agent)
        if match:
            browser_version = match.group(1)
    elif 'opera' in user_agent:
        browser = 'Opera'
        match = re.search(r'opera/([\d\.]+)', user_agent)
        if match:
            browser_version = match.group(1)
    
    # OS detection
    os_name = 'Unknown'
    os_version = 'Unknown'
    
    if 'windows nt' in user_agent:
        os_name = 'Windows'
        if 'windows nt 10.0' in user_agent:
            os_version = '10/11'
        elif 'windows nt 6.3' in user_agent:
            os_version = '8.1'
        elif 'windows nt 6.2' in user_agent:
            os_version = '8'
        elif 'windows nt 6.1' in user_agent:
            os_version = '7'
    elif 'mac os x' in user_agent or 'macos' in user_agent:
        os_name = 'macOS'
        match = re.search(r'mac os x ([\d_\.]+)', user_agent)
        if match:
            os_version = match.group(1).replace('_', '.')
    elif 'linux' in user_agent:
        os_name = 'Linux'
        if 'ubuntu' in user_agent:
            os_version = 'Ubuntu'
    elif 'android' in user_agent:
        os_name = 'Android'
        match = re.search(r'android ([\d\.]+)', user_agent)
        if match:
            os_version = match.group(1)
    elif 'iphone os' in user_agent or 'ios' in user_agent:
        os_name = 'iOS'
        match = re.search(r'os ([\d_]+)', user_agent)
        if match:
            os_version = match.group(1).replace('_', '.')
    
    # Device type detection
    is_mobile = bool(re.search(r'mobile|android|iphone|ipod|blackberry|windows phone', user_agent))
    is_tablet = bool(re.search(r'tablet|ipad|kindle|silk', user_agent))
    is_desktop = not (is_mobile or is_tablet)
    
    device_type = 'Desktop'
    if is_mobile:
        device_type = 'Mobile'
    elif is_tablet:
        device_type = 'Tablet'
    
    return {
        'browser': browser,
        'browser_version': browser_version,
        'os': os_name,
        'os_version': os_version,
        'device_type': device_type,
        'is_mobile': is_mobile,
        'is_tablet': is_tablet,
        'is_desktop': is_desktop
    }

# User agent parsing utility
import re

def parse_user_agent(user_agent):
    """Parse user agent string to extract browser, OS, and device information"""
    if not user_agent:
        return {
            'browser': 'Unknown',
            'browser_version': 'Unknown',
            'os': 'Unknown',
            'os_version': 'Unknown',
            'device_type': 'Unknown',
            'is_mobile': False,
            'is_tablet': False,
            'is_desktop': True
        }
    
    user_agent = user_agent.lower()
    
    # Browser detection
    browser = 'Unknown'
    browser_version = 'Unknown'
    
    if 'chrome' in user_agent and 'edge' not in user_agent:
        browser = 'Chrome'
        match = re.search(r'chrome/([\d\.]+)', user_agent)
        if match:
            browser_version = match.group(1)
    elif 'firefox' in user_agent:
        browser = 'Firefox'
        match = re.search(r'firefox/([\d\.]+)', user_agent)
        if match:
            browser_version = match.group(1)
    elif 'safari' in user_agent and 'chrome' not in user_agent:
        browser = 'Safari'
        match = re.search(r'version/([\d\.]+)', user_agent)
        if match:
            browser_version = match.group(1)
    elif 'edge' in user_agent:
        browser = 'Edge'
        match = re.search(r'edge/([\d\.]+)', user_agent)
        if match:
            browser_version = match.group(1)
    elif 'opera' in user_agent:
        browser = 'Opera'
        match = re.search(r'opera/([\d\.]+)', user_agent)
        if match:
            browser_version = match.group(1)
    
    # OS detection
    os_name = 'Unknown'
    os_version = 'Unknown'
    
    if 'windows nt' in user_agent:
        os_name = 'Windows'
        if 'windows nt 10.0' in user_agent:
            os_version = '10/11'
        elif 'windows nt 6.3' in user_agent:
            os_version = '8.1'
        elif 'windows nt 6.2' in user_agent:
            os_version = '8'
        elif 'windows nt 6.1' in user_agent:
            os_version = '7'
    elif 'mac os x' in user_agent or 'macos' in user_agent:
        os_name = 'macOS'
        match = re.search(r'mac os x ([\d_\.]+)', user_agent)
        if match:
            os_version = match.group(1).replace('_', '.')
    elif 'linux' in user_agent:
        os_name = 'Linux'
        if 'ubuntu' in user_agent:
            os_version = 'Ubuntu'
    elif 'android' in user_agent:
        os_name = 'Android'
        match = re.search(r'android ([\d\.]+)', user_agent)
        if match:
            os_version = match.group(1)
    elif 'iphone os' in user_agent or 'ios' in user_agent:
        os_name = 'iOS'
        match = re.search(r'os ([\d_]+)', user_agent)
        if match:
            os_version = match.group(1).replace('_', '.')
    
    # Device type detection
    is_mobile = bool(re.search(r'mobile|android|iphone|ipod|blackberry|windows phone', user_agent))
    is_tablet = bool(re.search(r'tablet|ipad|kindle|silk', user_agent))
    is_desktop = not (is_mobile or is_tablet)
    
    device_type = 'Desktop'
    if is_mobile:
        device_type = 'Mobile'
    elif is_tablet:
        device_type = 'Tablet'
    
    return {
        'browser': browser,
        'browser_version': browser_version,
        'os': os_name,
        'os_version': os_version,
        'device_type': device_type,
        'is_mobile': is_mobile,
        'is_tablet': is_tablet,
        'is_desktop': is_desktop
    }

def get_country_code_from_ip(ip_address):
    try:
        resp = requests.get(f"https://ipapi.co/{ip_address}/country/", timeout=2)
        if resp.status_code == 200:
            return resp.text.strip()  # e.g. "US"
    except Exception:
        pass
    return 'US'  # Default to US on failure