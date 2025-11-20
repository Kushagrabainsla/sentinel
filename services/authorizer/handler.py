import json
import os
import boto3
from botocore.exceptions import ClientError

# DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

def get_users_table():
    """Get users table from environment variable"""
    table_name = os.environ.get('DYNAMODB_USERS_TABLE')
    if not table_name:
        raise RuntimeError("DYNAMODB_USERS_TABLE environment variable not set")
    return dynamodb.Table(table_name)

def generate_policy(effect, resource, principal_id=None, context=None):
    """Generate IAM policy for API Gateway"""
    policy = {
        "principalId": principal_id or "user",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": resource
                }
            ]
        }
    }
    
    if context:
        policy["context"] = context
        
    return policy

def lambda_handler(event, context):
    """
    API Gateway Lambda Authorizer for API Key authentication
    
    Expected event structure:
    {
        "type": "REQUEST",
        "methodArn": "arn:aws:execute-api:...",
        "headers": {
            "x-api-key": "user-api-key"
        },
        "requestContext": {...}
    }
    """
    
    try:
        print(f"🔐 Authorizer invoked with event: {json.dumps(event, default=str)}")
        
        # Extract API key from headers
        headers = event.get('headers', {})
        api_key = (headers.get('x-api-key') or 
                  headers.get('X-API-Key') or 
                  headers.get('Authorization', '').replace('Bearer ', ''))
        
        if not api_key:
            print("❌ No API key provided")
            raise Exception('Unauthorized')
        
        # Get user by API key
        users_table = get_users_table()
        
        try:
            response = users_table.query(
                IndexName='api_key_index',
                KeyConditionExpression='api_key = :api_key',
                ExpressionAttributeValues={':api_key': api_key}
            )
            
            users = response.get('Items', [])
            if not users:
                print(f"❌ Invalid API key: {api_key[:8]}...")
                raise Exception('Unauthorized')
                
            user = users[0]
            
            # Check if user is active
            if user.get('status') != 'active':
                print(f"❌ Inactive user: {user.get('email')}")
                raise Exception('Unauthorized')
                
            print(f"✅ User authenticated: {user.get('email')} (ID: {user.get('id')})")
            
            # Generate allow policy with user context
            policy = generate_policy(
                effect='Allow',
                resource=event['methodArn'],
                principal_id=user['id'],
                context={
                    'user_id': user['id'],
                    'user_email': user['email'],
                    'user_status': user.get('status', 'active')
                }
            )
            
            return policy
            
        except ClientError as e:
            print(f"❌ DynamoDB error: {str(e)}")
            raise Exception('Unauthorized')
            
    except Exception as e:
        print(f"❌ Authorization failed: {str(e)}")
        # Return deny policy for any errors
        return generate_policy('Deny', event.get('methodArn', '*'))