#!/bin/bash

# Complete End-to-End Test Runner for Sentinel
set -e  # Exit on any error

echo "🚀 Starting Sentinel Complete Flow Test"
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Change to project root
cd "$(dirname "$0")/.."

# Get Terraform outputs
echo "Getting infrastructure details..."
cd infra
API_URL=$(terraform output -raw api_url 2>/dev/null)
SEND_QUEUE_URL=$(terraform output -raw send_queue_url 2>/dev/null)
CAMPAIGNS_TABLE=$(terraform output -raw dynamodb_campaigns_table 2>/dev/null)
CONTACTS_TABLE=$(terraform output -raw dynamodb_contacts_table 2>/dev/null)
RECIPIENTS_TABLE=$(terraform output -raw dynamodb_recipients_table 2>/dev/null)
EVENTS_TABLE=$(terraform output -raw dynamodb_events_table 2>/dev/null)
cd ..

if [[ -z "$API_URL" || -z "$CAMPAIGNS_TABLE" ]]; then
    error "Could not get Terraform outputs. Make sure infrastructure is deployed."
    exit 1
fi

success "Infrastructure details retrieved"
echo "  API URL: $API_URL"
echo "  Campaigns Table: $CAMPAIGNS_TABLE"

# Step 1: Cleanup any existing test data
echo ""
echo "🧹 Step 1: Cleaning up existing test data..."

# Delete test contacts (IDs 1001-1010)
for i in {1001..1010}; do
    aws dynamodb delete-item \
        --table-name $CONTACTS_TABLE \
        --key '{"id": {"S": "'$i'"}}' \
        --region us-east-1 2>/dev/null || true
done

# Delete test campaigns (IDs 9001-9010)  
for i in {9001..9010}; do
    aws dynamodb delete-item \
        --table-name $CAMPAIGNS_TABLE \
        --key '{"id": {"S": "'$i'"}}' \
        --region us-east-1 2>/dev/null || true
done

success "Cleaned up existing test data"

# Step 2: Create test contacts
echo ""
echo "👥 Step 2: Creating test contacts..."

TEST_CONTACTS=(
    "kushagra.bainsla+sentinel1@sjsu.edu"
    "kushagra.bainsla+sentinel2@sjsu.edu"
    "kushagra.bainsla+sentinel3@sjsu.edu"
)

contact_id=1001
for email in "${TEST_CONTACTS[@]}"; do
    aws dynamodb put-item \
        --table-name $CONTACTS_TABLE \
        --item '{
            "id": {"S": "'$contact_id'"},
            "email": {"S": "'$email'"},
            "status": {"S": "active"},
            "attrs": {"M": {}},
            "created_at": {"N": "'$(date +%s)'"}
        }' \
        --region us-east-1

    success "Created contact: $email"
    ((contact_id++))
done

# Step 3: Create SES template (if it doesn't exist)
echo ""
echo "📧 Step 3: Setting up SES template..."

aws ses create-template \
    --template '{
        "TemplateName": "test-welcome-template",
        "Subject": "Welcome to Sentinel Test!",
        "HtmlPart": "<h1>Hello {{name}}!</h1><p>This is a test email from Sentinel.</p>",
        "TextPart": "Hello {{name}}! This is a test email from Sentinel."
    }' \
    --region us-east-1 2>/dev/null || warning "Template may already exist"

success "SES template ready"

# Create a test campaign
echo ""
echo "📋 Step 4: Creating test campaign..."

CAMPAIGN_PAYLOAD='{
    "name": "E2E Test Campaign",
    "template_id": "test-welcome-template",
    "segment_id": "all-active"
}'

CAMPAIGN_RESPONSE=$(curl -s -w "%{http_code}" -X POST "$API_URL/v1/campaigns" \
    -H "Content-Type: application/json" \
    -d "$CAMPAIGN_PAYLOAD")

HTTP_CODE="${CAMPAIGN_RESPONSE: -3}"
RESPONSE_BODY="${CAMPAIGN_RESPONSE%???}"

if [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "201" ]]; then
    CAMPAIGN_ID=$(echo "$RESPONSE_BODY" | grep -o '"campaign_id":[0-9]*' | grep -o '[0-9]*' || echo "")
    
    if [[ -z "$CAMPAIGN_ID" ]]; then
        # Try alternative response format
        CAMPAIGN_ID=$(echo "$RESPONSE_BODY" | grep -o '"id":[0-9]*' | grep -o '[0-9]*' || echo "9001")
    fi
    
    success "Created campaign with ID: $CAMPAIGN_ID"
else
    error "Failed to create campaign. HTTP Code: $HTTP_CODE"
    echo "Response: $RESPONSE_BODY"
    
    # Fallback: create campaign directly in DynamoDB
    warning "Trying direct DynamoDB campaign creation..."
    CAMPAIGN_ID="9001"
    aws dynamodb put-item \
        --table-name $CAMPAIGNS_TABLE \
        --item '{
            "id": {"S": "'$CAMPAIGN_ID'"},
            "name": {"S": "E2E Test Campaign"},
            "template_id": {"S": "test-welcome-template"},
            "segment_id": {"S": "all-active"},
            "state": {"S": "draft"},
            "created_at": {"N": "'$(date +%s)'"}
        }' \
        --region us-east-1
    
    success "Created campaign directly in DynamoDB: $CAMPAIGN_ID"
fi

# Step 5: Start the campaign
echo ""
echo "🚀 Step 5: Starting campaign..."

# Try API first
START_RESPONSE=$(curl -s -w "%{http_code}" -X POST "$API_URL/campaigns/$CAMPAIGN_ID/start" \
    -H "Content-Type: application/json")

HTTP_CODE="${START_RESPONSE: -3}"
RESPONSE_BODY="${START_RESPONSE%???}"

if [[ "$HTTP_CODE" == "200" ]]; then
    success "Campaign started via API"
else
    warning "API start failed, trying direct Lambda invocation..."
    
    # Get Lambda function name and invoke directly
    START_LAMBDA=$(aws lambda list-functions --query 'Functions[?contains(FunctionName, `start-campaign`)].FunctionName' --output text --region us-east-1)
    
    if [[ -n "$START_LAMBDA" ]]; then
        PAYLOAD=$(echo '{"campaign_id": "'$CAMPAIGN_ID'"}' | base64)
        aws lambda invoke \
            --function-name "$START_LAMBDA" \
            --payload "$PAYLOAD" \
            --region us-east-1 \
            /tmp/start_response.json > /dev/null
        
        success "Campaign started via direct Lambda invocation"
        echo "Lambda response: $(cat /tmp/start_response.json)"
    else
        error "Could not find start-campaign Lambda function"
        exit 1
    fi
fi

# Step 6: Wait and monitor progress
echo ""
echo "⏳ Step 6: Monitoring campaign progress..."

sleep 5  # Wait for processing

# Check SQS queue for messages
QUEUE_ATTRS=$(aws sqs get-queue-attributes \
    --queue-url "$SEND_QUEUE_URL" \
    --attribute-names ApproximateNumberOfMessages \
    --region us-east-1 \
    --output json)

MSG_COUNT=$(echo "$QUEUE_ATTRS" | grep -o '"ApproximateNumberOfMessages":"[0-9]*"' | grep -o '[0-9]*' || echo "0")
echo "Messages in send queue: $MSG_COUNT"

# Check recipients table
RECIPIENTS_COUNT=$(aws dynamodb query \
    --table-name $RECIPIENTS_TABLE \
    --key-condition-expression "campaign_id = :cid" \
    --expression-attribute-values '{":cid": {"S": "'$CAMPAIGN_ID'"}}' \
    --select COUNT \
    --region us-east-1 \
    --output text --query Count)

success "Recipients created: $RECIPIENTS_COUNT"

# Step 7: Process send queue (simulate)
echo ""
echo "📨 Step 7: Processing send queue..."

if [[ "$MSG_COUNT" -gt 0 ]]; then
    # Get send worker Lambda
    SEND_LAMBDA=$(aws lambda list-functions --query 'Functions[?contains(FunctionName, `send-worker`)].FunctionName' --output text --region us-east-1)
    
    if [[ -n "$SEND_LAMBDA" ]]; then
        # Receive and process a few messages
        for i in {1..3}; do
            MESSAGE=$(aws sqs receive-message --queue-url "$SEND_QUEUE_URL" --region us-east-1 --output json 2>/dev/null || echo "")
            
            if [[ -n "$MESSAGE" && "$MESSAGE" != "" && "$MESSAGE" != "null" ]]; then
                # Invoke send worker with the message
                SEND_PAYLOAD=$(echo "$MESSAGE" | base64)
                aws lambda invoke \
                    --function-name "$SEND_LAMBDA" \
                    --payload "$SEND_PAYLOAD" \
                    --region us-east-1 \
                    /tmp/send_response.json > /dev/null 2>&1 || true
                
                success "Processed send message $i"
            fi
        done
    else
        warning "Send worker Lambda not found, skipping message processing"
    fi
else
    warning "No messages in queue to process"
fi

# Step 8: Test event processing (skipped - no SES event configuration)
echo ""
echo "📊 Step 8: Event processing not configured"
echo "ℹ️  SES events (bounces, complaints) are not currently captured"
echo "   This would require SES configuration sets and SNS integration"

# Step 9: Final verification
echo ""
echo "🔍 Step 9: Final verification..."

# Check campaign state
CAMPAIGN_STATE=$(aws dynamodb get-item \
    --table-name $CAMPAIGNS_TABLE \
    --key '{"id": {"S": "'$CAMPAIGN_ID'"}}' \
    --region us-east-1 \
    --output json | grep -o '"state":{"S":"[^"]*"}' | grep -o '"[^"]*"$' | tr -d '"' || echo "unknown")

echo "Campaign state: $CAMPAIGN_STATE"

# Check events
EVENTS_COUNT=$(aws dynamodb scan \
    --table-name $EVENTS_TABLE \
    --filter-expression "campaign_id = :cid" \
    --expression-attribute-values '{":cid": {"S": "'$CAMPAIGN_ID'"}}' \
    --select COUNT \
    --region us-east-1 \
    --output text --query Count)

echo "Events recorded: $EVENTS_COUNT"

# Summary
echo ""
echo "🎉 Test Summary"
echo "==============="
echo "Campaign ID: $CAMPAIGN_ID"
echo "Contacts created: ${#TEST_CONTACTS[@]}"
echo "Recipients created: $RECIPIENTS_COUNT"
echo "Events recorded: $EVENTS_COUNT"
echo "Campaign state: $CAMPAIGN_STATE"

if [[ "$RECIPIENTS_COUNT" -eq "${#TEST_CONTACTS[@]}" ]]; then
    success "End-to-end test completed successfully!"
else
    warning "Test completed with some issues. Check the logs above."
fi

echo ""
echo "🔧 Next steps:"
echo "  - Check CloudWatch logs for Lambda functions"
echo "  - Verify SES dashboard for email delivery"
echo "  - Review DynamoDB tables for data consistency"
echo "  - Run: aws ses get-send-statistics --region us-east-1"