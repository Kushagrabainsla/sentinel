#!/usr/bin/env python3
"""
DynamoDB Table Verification Script
Since we're using DynamoDB, this script verifies that all required tables exist
and are accessible.
"""
import os
import sys
import boto3
from botocore.exceptions import ClientError

def verify_dynamodb_tables():
    """Verify all required DynamoDB tables exist and are accessible"""
    
    # Get AWS region
    region = os.environ.get('AWS_REGION', 'us-east-1')
    
    # Initialize DynamoDB client
    try:
        dynamodb = boto3.client('dynamodb', region_name=region)
    except Exception as e:
        print(f"❌ Failed to initialize DynamoDB client: {e}")
        return False
    
    # Required table environment variables
    required_tables = [
        ('DYNAMODB_CAMPAIGNS_TABLE', 'Campaigns'),
        ('DYNAMODB_CONTACTS_TABLE', 'Contacts'), 
        ('DYNAMODB_RECIPIENTS_TABLE', 'Recipients'),
        ('DYNAMODB_EVENTS_TABLE', 'Events')
    ]
    
    print("🔍 Verifying DynamoDB tables...")
    
    all_tables_ok = True
    
    for env_var, table_desc in required_tables:
        table_name = os.environ.get(env_var)
        
        if not table_name:
            print(f"❌ Environment variable {env_var} not set")
            all_tables_ok = False
            continue
            
        try:
            # Check if table exists and get its status
            response = dynamodb.describe_table(TableName=table_name)
            table_status = response['Table']['TableStatus']
            
            if table_status == 'ACTIVE':
                print(f"✅ {table_desc} table ({table_name}) is ACTIVE")
            else:
                print(f"⚠️  {table_desc} table ({table_name}) status: {table_status}")
                
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"❌ {table_desc} table ({table_name}) does not exist")
            else:
                print(f"❌ Error checking {table_desc} table ({table_name}): {e}")
            all_tables_ok = False
            
    return all_tables_ok

if __name__ == "__main__":
    print("Sentinel DynamoDB Verification")
    print("=" * 40)
    
    success = verify_dynamodb_tables()
    
    if success:
        print("\n✅ All DynamoDB tables are ready!")
        sys.exit(0)
    else:
        print("\n❌ DynamoDB table verification failed!")
        sys.exit(1)
