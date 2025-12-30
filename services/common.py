#!/usr/bin/env python3
"""
Common utilities and enums for Sentinel services

This module contains all shared utility functions and enum definitions used across
different services in the Sentinel email marketing platform.

**Deployment Note:**  
This file is copied into all Lambda functions as a shared utility module during deployment.
It is intended to be self-contained and should NOT import or depend on any external libraries
that are not part of the AWS Lambda Python runtime.  
Adding external dependencies here will break Lambda deployments that do not have a
requirements.txt for those libraries.

Consolidated into a single file for simplified deployment.
"""

import json
import os
import re
import time
import random
import hashlib
import base64
import urllib.request
import urllib.parse
from decimal import Decimal
from enum import Enum
import boto3
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
    AB_TEST = "AB"   # A/B Testing

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
    SENT = "sent"

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

def is_unsubscribed(campaign_id, email):
    """Check if recipient has unsubscribed from this campaign"""
    try:
        from boto3.dynamodb.conditions import Key, Attr
        table = get_table('DYNAMODB_EVENTS_TABLE')
        response = table.query(
            IndexName='campaign_index',
            KeyConditionExpression=Key('campaign_id').eq(str(campaign_id)),
            FilterExpression=Attr('type').eq(EventType.UNSUBSCRIBE.value) & Attr('email').eq(email)
        )
        return len(response.get('Items', [])) > 0
    except Exception as e:
        print(f"⚠️ Error checking unsubscribe status for {email}: {e}")
        return False

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


# ================================
# HTML SANITIZATION UTILITIES
# ================================

# Allowed HTML tags for email content (safe subset)
ALLOWED_HTML_TAGS = {
    'a', 'abbr', 'b', 'blockquote', 'br', 'caption', 'center', 'cite', 'code',
    'col', 'colgroup', 'dd', 'div', 'dl', 'dt', 'em', 'h1', 'h2', 'h3', 'h4',
    'h5', 'h6', 'hr', 'i', 'img', 'li', 'ol', 'p', 'pre', 'q', 's', 'small',
    'span', 'strike', 'strong', 'sub', 'sup', 'table', 'tbody', 'td', 'tfoot',
    'th', 'thead', 'tr', 'u', 'ul'
}

# Dangerous URL schemes
DANGEROUS_URL_SCHEMES = {
    'javascript:', 'data:', 'vbscript:', 'file:', 'about:'
}

# Suspicious patterns that might indicate phishing or XSS
SUSPICIOUS_HTML_PATTERNS = [
    r'onclick\s*=',
    r'onerror\s*=',
    r'onload\s*=',
    r'<script',
    r'<iframe',
    r'<object',
    r'<embed',
    r'<applet',
    r'document\.cookie',
    r'window\.location',
    r'eval\(',
]

def sanitize_html_content(html_content):
    """
    Sanitize HTML content to prevent XSS and injection attacks
    
    Args:
        html_content: Raw HTML string to sanitize
    
    Returns:
        dict with keys:
            - is_valid: bool indicating if content is safe
            - sanitized_html: cleaned HTML string
            - warnings: list of warning messages
            - blocked_elements: list of blocked elements
    """
    if not html_content:
        return {
            "is_valid": True,
            "sanitized_html": "",
            "warnings": [],
            "blocked_elements": []
        }
    
    warnings = []
    blocked_elements = []
    
    # Step 1: Detect suspicious patterns
    for pattern in SUSPICIOUS_HTML_PATTERNS:
        if re.search(pattern, html_content, re.IGNORECASE):
            warnings.append(f"Suspicious pattern detected: {pattern}")
            blocked_elements.append(f"Pattern: {pattern}")
    
    # Step 2: Remove dangerous tags
    dangerous_tags = ['script', 'iframe', 'object', 'embed', 'applet', 'form', 'input', 'button']
    for tag in dangerous_tags:
        pattern = rf'<{tag}[^>]*>.*?</{tag}>|<{tag}[^>]*/?>'
        if re.search(pattern, html_content, re.IGNORECASE | re.DOTALL):
            warnings.append(f"Removed dangerous tag: <{tag}>")
            blocked_elements.append(f"<{tag}>")
        html_content = re.sub(pattern, '', html_content, flags=re.IGNORECASE | re.DOTALL)
    
    # Step 3: Remove event handlers
    event_handlers = [
        'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover',
        'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup',
        'onload', 'onunload', 'onerror', 'onabort', 'onblur', 'onchange',
        'onfocus', 'onreset', 'onselect', 'onsubmit'
    ]
    
    for handler in event_handlers:
        pattern = rf'{handler}\s*=\s*["\'][^"\']*["\']'
        if re.search(pattern, html_content, re.IGNORECASE):
            warnings.append(f"Removed event handler: {handler}")
        html_content = re.sub(pattern, '', html_content, flags=re.IGNORECASE)
    
    # Step 4: Sanitize dangerous URLs
    def check_and_remove_dangerous_url(match):
        full_tag = match.group(0)
        url = match.group(1)
        
        if not url:
            return full_tag
        
        url_lower = url.strip().lower()
        
        # Check for dangerous schemes
        for scheme in DANGEROUS_URL_SCHEMES:
            if url_lower.startswith(scheme):
                warnings.append(f"Blocked dangerous URL scheme: {scheme}")
                blocked_elements.append(f"URL: {url[:50]}...")
                return full_tag.replace(f'href="{url}"', '').replace(f"href='{url}'", '')
        
        # Check for obfuscated URLs
        if re.search(r'%00|%0[ad]|\\x|\\u', url, re.IGNORECASE):
            warnings.append("Blocked obfuscated URL")
            blocked_elements.append(f"Obfuscated URL: {url[:50]}...")
            return full_tag.replace(f'href="{url}"', '').replace(f"href='{url}'", '')
        
        return full_tag
    
    # Sanitize href attributes
    html_content = re.sub(
        r'<a\s+[^>]*href\s*=\s*["\']([^"\']+)["\'][^>]*>',
        check_and_remove_dangerous_url,
        html_content,
        flags=re.IGNORECASE
    )
    
    # Sanitize src attributes (for images)
    def check_and_remove_dangerous_src(match):
        full_tag = match.group(0)
        url = match.group(1)
        
        if not url:
            return full_tag
        
        url_lower = url.strip().lower()
        
        # Check for data URIs (only allow images)
        if url_lower.startswith('data:'):
            if not url_lower.startswith('data:image/'):
                warnings.append("Blocked non-image data URI")
                blocked_elements.append(f"Data URI: {url[:50]}...")
                return full_tag.replace(f'src="{url}"', '').replace(f"src='{url}'", '')
        
        return full_tag
    
    html_content = re.sub(
        r'<img\s+[^>]*src\s*=\s*["\']([^"\']+)["\'][^>]*>',
        check_and_remove_dangerous_src,
        html_content,
        flags=re.IGNORECASE
    )
    
    # Determine if content is valid (no blocked elements)
    is_valid = len(blocked_elements) == 0
    
    return {
        "is_valid": is_valid,
        "sanitized_html": html_content,
        "warnings": warnings,
        "blocked_elements": blocked_elements
    }

# ================================
# RETRY UTILITIES WITH EXPONENTIAL BACKOFF
# ================================


# Transient errors that should be retried
RETRYABLE_ERROR_CODES = {
    'Throttling',
    'ThrottlingException', 
    'RequestLimitExceeded',
    'ServiceUnavailable',
    'RequestTimeout',
    'InternalServerError',
    'InternalError',
    'ProvisionedThroughputExceededException',
    'TooManyRequestsException',
}

# Permanent errors that should NOT be retried
PERMANENT_ERROR_CODES = {
    'InvalidParameterValue',
    'ValidationError',
    'AccessDenied',
    'UnauthorizedOperation',
    'InvalidClientTokenId',
    'MessageRejected',  # SES: Invalid email address
    'MailFromDomainNotVerified',  # SES: Domain not verified
}

def is_retryable_error(error):
    """
    Determine if an error should be retried.
    Handles AWS ClientError, urllib HTTPError, and general network exceptions.
    """
    # 1. Handle urllib.error.HTTPError (from our new Gmail API calls)
    if hasattr(error, 'code'):
        status_code = getattr(error, 'code')
        # Retry on 429 (rate limit) and 5xx (server errors)
        return status_code == 429 or status_code >= 500

    # 2. Handle botocore.exceptions.ClientError
    if hasattr(error, 'response'):
        error_code = error.response.get('Error', {}).get('Code', '')
        
        # Don't retry known permanent errors
        if error_code in PERMANENT_ERROR_CODES:
            return False
        
        # Retry known transient errors
        if error_code in RETRYABLE_ERROR_CODES:
            return True
        
        # Check HTTP status code in AWS response
        status_code = error.response.get('ResponseMetadata', {}).get('HTTPStatusCode', 0)
        return status_code >= 500 or status_code == 429

    # 3. Default: Retry network errors / unknown exceptions (timeouts, connection issues)
    return True
    
    # Default: retry unknown errors
    return True

def exponential_backoff_retry(
    func,
    max_retries=3,
    base_delay=1.0,
    max_delay=60.0,
    exponential_base=2,
    jitter=True,
    retryable_exceptions=(Exception,)
):
    """
    Execute a function with exponential backoff retry logic
    
    Args:
        func: Callable to execute
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        exponential_base: Base for exponential calculation (default: 2)
        jitter: Add random jitter to prevent thundering herd (default: True)
        retryable_exceptions: Tuple of exception types to retry (default: all)
    
    Returns:
        Result of func() if successful
    
    Raises:
        Last exception if all retries exhausted
    
    Example:
        result = exponential_backoff_retry(
            lambda: ses.send_email(**params),
            max_retries=3
        )
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):  # +1 because first attempt is not a retry
        try:
            return func()
        
        except retryable_exceptions as e:
            last_exception = e
            
            # Check if this error should be retried
            if not is_retryable_error(e):
                print(f"❌ Permanent error, not retrying: {e}")
                raise
            
            # If this was the last attempt, raise the error
            if attempt >= max_retries:
                print(f"❌ Max retries ({max_retries}) exhausted")
                raise
            
            # Calculate delay with exponential backoff
            delay = min(base_delay * (exponential_base ** attempt), max_delay)
            
            # Add jitter to prevent thundering herd problem
            if jitter:
                delay = delay * (0.5 + random.random())  # Random between 50% and 150% of delay
            
            # Log retry attempt
            error_code = getattr(e, 'response', {}).get('Error', {}).get('Code', type(e).__name__)
            print(f"⏳ Retry {attempt + 1}/{max_retries} after {delay:.2f}s due to {error_code}")
            
            # Wait before retrying
            time.sleep(delay)
    
    # Should never reach here, but just in case
    if last_exception:
        raise last_exception

def retry_with_backoff(max_retries=3, base_delay=1.0):
    """
    Decorator for adding exponential backoff retry to functions
    
    Usage:
        @retry_with_backoff(max_retries=3, base_delay=1.0)
        def send_email(params):
            return ses.send_email(**params)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            return exponential_backoff_retry(
                lambda: func(*args, **kwargs),
                max_retries=max_retries,
                base_delay=base_delay
            )
        return wrapper
    return decorator

# ================================
# BATCH PROCESSING UTILITIES
# ================================

def process_in_batches(items, batch_size, processor_func, continue_on_error=True):
    """
    Process items in batches with error handling
    
    Args:
        items: List of items to process
        batch_size: Number of items per batch
        processor_func: Function to process each batch (receives list of items)
        continue_on_error: If True, continue processing remaining batches on error
    
    Returns:
        dict with keys:
            - successful: Number of successfully processed items
            - failed: Number of failed items
            - errors: List of error messages
    
    Example:
        result = process_in_batches(
            emails,
            batch_size=25,
            processor_func=lambda batch: send_batch_to_sqs(batch)
        )
    """
    successful = 0
    failed = 0
    errors = []
    
    # Split items into batches
    batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
    
    print(f"📦 Processing {len(items)} items in {len(batches)} batches of {batch_size}")
    
    for batch_num, batch in enumerate(batches, 1):
        try:
            processor_func(batch)
            successful += len(batch)
            print(f"✅ Batch {batch_num}/{len(batches)}: {len(batch)} items processed")
        
        except Exception as e:
            failed += len(batch)
            error_msg = f"Batch {batch_num}/{len(batches)} failed: {str(e)}"
            errors.append(error_msg)
            print(f"❌ {error_msg}")
            
            if not continue_on_error:
                raise
    
    return {
        "successful": successful,
        "failed": failed,
        "errors": errors,
        "total_batches": len(batches)
    }


# ================================
# EMAIL UTILITIES
# ================================

def add_dynamic_image(html_content, image_url, alt_text="Dynamic Content", position="top", 
                     campaign_id=None, recipient_id=None, email=None):
    """
    Adds a dynamic image to email HTML content using redirect pattern.
    
    Uses HTTP 302 redirect to bypass Gmail's image caching:
    1. Email contains base URL
    2. Server returns redirect with fresh timestamp
    3. Each open follows redirect to new URL
    4. Image reflects actual open time
    
    Args:
        html_content: The HTML email content
        image_url: Base URL that returns 302 redirect
        alt_text: Alt text for the image
        position: Where to insert ('top', 'bottom', or 'replace_placeholder')
        campaign_id: Campaign ID for tracking
        recipient_id: Recipient ID (makes URL unique per recipient)
        email: Recipient email (alternative to recipient_id)
    
    Returns:
        Modified HTML with dynamic image
    """
    
    # Build URL parameters
    params = []
    
    # Add recipient ID to make URL unique per recipient
    if recipient_id:
        params.append(f"rid={recipient_id}")
    elif email:
        # Hash email for privacy
        email_hash = hashlib.md5(email.encode()).hexdigest()[:8]
        params.append(f"rid={email_hash}")
    
    if campaign_id:
        params.append(f"cid={campaign_id}")
    
    # Combine base URL with parameters
    separator = '&' if '?' in image_url else '?'
    dynamic_url = f"{image_url}{separator}{'&'.join(params)}" if params else image_url
    
    img_tag = f'''
    <div style="text-align: center; margin: 20px 0;">
        <img src="{dynamic_url}" 
             alt="{alt_text}" 
             style="max-width: 100%; height: auto; display: block; margin: 0 auto;"
             loading="eager" />
    </div>
    '''
    
    if position == "top":
        # Insert after opening body tag
        if '<body' in html_content:
            html_content = html_content.replace('<body>', f'<body>{img_tag}', 1)
        else:
            html_content = img_tag + html_content
    elif position == "bottom":
        # Insert before closing body tag
        if '</body>' in html_content:
            html_content = html_content.replace('</body>', f'{img_tag}</body>', 1)
        else:
            html_content = html_content + img_tag
    elif position == "replace_placeholder":
        # Replace a placeholder like {{dynamic_image}}
        html_content = html_content.replace('{{dynamic_image}}', img_tag)
    
    return html_content


def create_tracking_pixel(campaign_id, subscriber_id, base_url):
    """
    Creates a 1x1 tracking pixel for email opens.
    
    Args:
        campaign_id: Campaign identifier
        subscriber_id: Subscriber identifier  
        base_url: Base tracking URL
    
    Returns:
        HTML img tag for tracking pixel
    """
    pixel_url = f"{base_url}/track/open?cid={campaign_id}&sid={subscriber_id}&t={int(time.time())}"
    return f'<img src="{pixel_url}" width="1" height="1" alt="" style="display:none;" />'

def create_raw_email_message(from_email, to_email, subject, html_body, text_body=None, unsubscribe_url=None):
    """Create a MIME message with standard compliant headers"""
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = from_email
    message["To"] = to_email
    
    # Add List-Unsubscribe headers for RFC 8058 compliance
    if unsubscribe_url:
        message["List-Unsubscribe"] = f"<{unsubscribe_url}>"
        message["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    
    if text_body:
        message.attach(MIMEText(text_body, "plain"))
    if html_body:
        message.attach(MIMEText(html_body, "html"))
        
    return message

# ================================
# GMAIL API UTILITIES
# ================================

def refresh_google_token(refresh_token):
    """Refresh Google OAuth access token using standard urllib"""
    try:
        client = boto3.client('secretsmanager', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        response = client.get_secret_value(SecretId='sentinel_config')
        config = json.loads(response['SecretString'])
        
        client_id = config.get('GOOGLE_CLIENT_ID')
        client_secret = config.get('GOOGLE_CLIENT_SECRET')
        
        if not refresh_token or not client_id or not client_secret:
            return None
            
        data = urllib.parse.urlencode({
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }).encode()
        
        req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            return {
                "access_token": res_data.get('access_token'),
                "expires_in": res_data.get('expires_in')
            }
    except Exception as e:
        print(f"Error refreshing Google token: {e}")
        return None

def send_gmail(user_data, recipient_email, subject, html_body, text_body=None, unsubscribe_url=None):
    """Send email via Gmail API using raw message"""
    access_token = user_data.get('google_access_token')
    refresh_token = user_data.get('google_refresh_token')
    expiry = user_data.get('google_token_expiry', 0)
    
    # Refresh token if needed
    if time.time() > (int(expiry) - 60):
        new_token_data = refresh_google_token(refresh_token)
        if new_token_data:
            access_token = new_token_data['access_token']
        else:
            return False, "Failed to refresh Google token"

    # Create message using common utility
    from_email = user_data.get('google_email', recipient_email)
    message = create_raw_email_message(from_email, recipient_email, subject, html_body, text_body, unsubscribe_url)
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    
    try:
        url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
        payload = json.dumps({"raw": raw_message}).encode()
        
        req = urllib.request.Request(
            url, 
            data=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            return True, res_data.get('id')
            
    except Exception as e:
        return False, str(e)

def send_ses_raw(ses_client, from_email, to_email, subject, html_body, text_body=None, unsubscribe_url=None):
    """Send email via AWS SES using RawMessage to support custom headers"""
    message = create_raw_email_message(from_email, to_email, subject, html_body, text_body, unsubscribe_url)
    
    response = ses_client.send_raw_email(
        Source=from_email,
        Destinations=[to_email],
        RawMessage={"Data": message.as_bytes()}
    )
    return response.get("MessageId")
