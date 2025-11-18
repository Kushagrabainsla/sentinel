import os
import boto3
from boto3.dynamodb.conditions import Key, Attr

def get_dynamodb_resource():
    """Get DynamoDB resource"""
    return boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

def get_table(table_name):
    """Get DynamoDB table"""
    dynamodb = get_dynamodb_resource()
    return dynamodb.Table(table_name)

def get_campaigns_table():
    """Get campaigns table"""
    return get_table(os.environ['DYNAMODB_CAMPAIGNS_TABLE'])

def get_contacts_table():
    """Get contacts table"""
    return get_table(os.environ['DYNAMODB_CONTACTS_TABLE'])

def get_recipients_table():
    """Get recipients table"""
    return get_table(os.environ['DYNAMODB_RECIPIENTS_TABLE'])

def get_events_table():
    """Get events table"""
    return get_table(os.environ['DYNAMODB_EVENTS_TABLE'])
