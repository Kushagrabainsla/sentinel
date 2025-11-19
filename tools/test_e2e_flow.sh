#!/bin/bash

# End-to-End Testing for Sentinel Email Marketing System
echo "=== Sentinel E2E Testing ==="

# Configuration - Update these based on your Terraform outputs
cd infra
API_URL=$(terraform output -raw api_url 2>/dev/null || echo "https://your-api-gateway-url")
CAMPAIGNS_TABLE=$(terraform output -raw dynamodb_campaigns_table 2>/dev/null || echo "sentinel-campaigns")
CONTACTS_TABLE=$(terraform output -raw dynamodb_contacts_table 2>/dev/null || echo "sentinel-contacts")
RECIPIENTS_TABLE=$(terraform output -raw dynamodb_recipients_table 2>/dev/null || echo "sentinel-recipients")
EVENTS_TABLE=$(terraform output -raw dynamodb_events_table 2>/dev/null || echo "sentinel-events")
cd ..

echo "Using API URL: $API_URL"

# Step 1: Create test contacts
echo "=== Step 1: Creating Test Contacts ==="
aws dynamodb put-item \
  --table-name $CONTACTS_TABLE \
  --item '{
    "id": {"N": "1"},
    "email": {"S": "test1@example.com"},
    "status": {"S": "active"},
    "attrs": {"M": {}},
    "created_at": {"N": "'$(date +%s)'"}
  }' \
  --region us-east-1

aws dynamodb put-item \
  --table-name $CONTACTS_TABLE \
  --item '{
    "id": {"N": "2"}, 
    "email": {"S": "test2@example.com"},
    "status": {"S": "active"},
    "attrs": {"M": {}},
    "created_at": {"N": "'$(date +%s)'"}
  }' \
  --region us-east-1

echo "✓ Created test contacts"

# Step 2: Create a campaign
echo "=== Step 2: Creating Campaign ==="
CAMPAIGN_RESPONSE=$(curl -s -X POST "$API_URL/campaigns" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Campaign",
    "template_id": "welcome-template",
    "segment_id": "all-active"
  }')

echo "Campaign creation response: $CAMPAIGN_RESPONSE"

# Extract campaign ID (assuming it returns {"campaign_id": 123})
CAMPAIGN_ID=$(echo $CAMPAIGN_RESPONSE | grep -o '"campaign_id":[0-9]*' | grep -o '[0-9]*')

if [ -z "$CAMPAIGN_ID" ]; then
  echo "❌ Failed to create campaign"
  exit 1
fi

echo "✓ Created campaign with ID: $CAMPAIGN_ID"

# Step 3: Start the campaign
echo "=== Step 3: Starting Campaign ==="
START_RESPONSE=$(curl -s -X POST "$API_URL/campaigns/$CAMPAIGN_ID/start" \
  -H "Content-Type: application/json")

echo "Campaign start response: $START_RESPONSE"
echo "✓ Campaign started - check SQS for messages"

# Step 4: Monitor campaign progress
echo "=== Step 4: Monitoring Campaign Progress ==="

# Check recipients table for created records
echo "Checking recipients table..."
aws dynamodb query \
  --table-name $RECIPIENTS_TABLE \
  --key-condition-expression "campaign_id = :cid" \
  --expression-attribute-values '{
    ":cid": {"S": "'$CAMPAIGN_ID'"}
  }' \
  --region us-east-1

# Step 5: Event Processing (not configured)
echo "=== Step 5: Event Processing Status ==="
echo "ℹ️  SES event processing is not currently configured"
echo "   Email bounces and complaints are not automatically captured"
echo "   To enable this, SES configuration sets and SNS integration would be needed"

# Step 6: Check final state
echo "=== Step 6: Final State Check ==="

# Check campaign state
aws dynamodb get-item \
  --table-name $CAMPAIGNS_TABLE \
  --key '{"id": {"N": "'$CAMPAIGN_ID'"}}' \
  --region us-east-1

# Check events table
aws dynamodb scan \
  --table-name $EVENTS_TABLE \
  --filter-expression "campaign_id = :cid" \
  --expression-attribute-values '{
    ":cid": {"S": "'$CAMPAIGN_ID'"}
  }' \
  --region us-east-1

echo "=== E2E Test Complete ==="
echo "Campaign ID: $CAMPAIGN_ID"
echo "Check your SES dashboard for actual email delivery status"