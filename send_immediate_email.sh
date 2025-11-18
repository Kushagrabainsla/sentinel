#!/bin/bash
set -e

# Comprehensive Sentinel Email Testing Script
# Tests enhanced tracking pixels and email delivery

TARGET_EMAIL="kushagra.bainsla@sjsu.edu"
AWS_REGION="us-east-1"
CLEANUP_OLD_CONTACTS=true  # Set to false to keep existing test contacts

# Default tracking mode (can be overridden with argument)
TRACKING_MODE="${1:-smart}"

echo "🎯 Sentinel Enhanced Email Testing"
echo "================================="
echo "Target: $TARGET_EMAIL"
echo "Region: $AWS_REGION" 
echo "Tracking Mode: $TRACKING_MODE"
echo ""

# Validate tracking mode
case "$TRACKING_MODE" in
    "smart"|"inline"|"external"|"disabled")
        echo "✅ Valid tracking mode: $TRACKING_MODE"
        ;;
    *)
        echo "❌ Invalid tracking mode: $TRACKING_MODE"
        echo "Valid options: smart, inline, external, disabled"
        echo ""
        echo "Usage: $0 [tracking_mode]"
        echo "Examples:"
        echo "  $0 smart     # Smart hybrid tracking (recommended)"
        echo "  $0 inline    # Inline data URI (no external requests)"
        echo "  $0 external  # Traditional external pixel"
        echo "  $0 disabled  # No tracking pixels"
        exit 1
        ;;
esac
echo ""

# Get Terraform outputs
echo "🏗️ Getting infrastructure details..."
cd infra
API_URL=$(terraform output -raw api_url 2>/dev/null || echo "")
CAMPAIGNS_TABLE=$(terraform output -raw dynamodb_campaigns_table 2>/dev/null || echo "sentinel-campaigns")
CONTACTS_TABLE=$(terraform output -raw dynamodb_contacts_table 2>/dev/null || echo "sentinel-contacts")
cd ..

echo "API URL: $API_URL"
echo "Campaigns Table: $CAMPAIGNS_TABLE"
echo "Contacts Table: $CONTACTS_TABLE"
echo ""

# Optional: Clean up old test contacts
if [[ "$CLEANUP_OLD_CONTACTS" == "true" ]]; then
    echo "🧹 Cleaning up old test contacts..."
    
    # Get all contacts with the target email
    OLD_CONTACTS=$(aws dynamodb scan \
        --table-name "$CONTACTS_TABLE" \
        --filter-expression "email = :email" \
        --expression-attribute-values "{\":email\": {\"S\": \"$TARGET_EMAIL\"}}" \
        --region $AWS_REGION \
        --output json 2>/dev/null || echo '{"Items":[]}')
    
    OLD_COUNT=$(echo "$OLD_CONTACTS" | jq '.Items | length')
    
    if [[ "$OLD_COUNT" -gt 0 ]]; then
        echo "   Found $OLD_COUNT existing contacts with $TARGET_EMAIL"
        
        # Delete each old contact
        echo "$OLD_CONTACTS" | jq -r '.Items[].id.S' | while read -r contact_id; do
            if [[ -n "$contact_id" ]]; then
                aws dynamodb delete-item \
                    --table-name "$CONTACTS_TABLE" \
                    --key "{\"id\": {\"S\": \"$contact_id\"}}" \
                    --region $AWS_REGION >/dev/null 2>&1
                echo "   🗑️ Deleted contact: $contact_id"
            fi
        done
        
        echo "✅ Cleanup completed - removed $OLD_COUNT old contacts"
    else
        echo "   No old contacts found to clean up"
    fi
    echo ""
fi

# Step 1: Create test contact
echo "📋 Step 1: Creating test contact..."
CONTACT_ID="immediate-$(date +%s)"

aws dynamodb put-item \
    --table-name "$CONTACTS_TABLE" \
    --item '{
        "id": {"S": "'$CONTACT_ID'"},
        "email": {"S": "'$TARGET_EMAIL'"},
        "status": {"S": "active"},
        "attrs": {"M": {}},
        "created_at": {"N": "'$(date +%s)'"}
    }' \
    --region $AWS_REGION

echo "✅ Created contact: $TARGET_EMAIL (ID: $CONTACT_ID)"
echo ""

# Step 2: Try API method
if [[ -n "$API_URL" ]]; then
    echo "🌐 Step 2: Sending via API Gateway..."
    
    # Generate mode-specific content
    case "$TRACKING_MODE" in
        "smart")
            SUBJECT="🎯 Smart Hybrid Tracking Test"
            MODE_DESCRIPTION="Smart tracking combines inline and external pixels for the best balance of compatibility and analytics."
            MODE_COLOR="#059669"
            ;;
        "inline")
            SUBJECT="📦 Inline Tracking Test - Zero External Requests"  
            MODE_DESCRIPTION="Inline tracking uses data URIs with zero external requests - guaranteed no security warnings!"
            MODE_COLOR="#7c3aed"
            ;;
        "external")
            SUBJECT="🖼️ External Pixel Tracking Test"
            MODE_DESCRIPTION="Traditional external pixel tracking provides full server-side analytics but may trigger warnings."
            MODE_COLOR="#dc2626" 
            ;;
        "disabled")
            SUBJECT="🚫 Clean Email - No Tracking"
            MODE_DESCRIPTION="Clean email delivery with no tracking pixels for maximum compatibility."
            MODE_COLOR="#6b7280"
            ;;
    esac

    CAMPAIGN_PAYLOAD=$(cat <<EOF
{
    "name": "Enhanced Email Test - $TRACKING_MODE Mode for $TARGET_EMAIL",
    "subject": "$SUBJECT",
    "html_body": "<html><head><meta charset='utf-8'><title>Sentinel Tracking Test</title></head><body style='font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;'><div style='border: 2px solid $MODE_COLOR; border-radius: 8px; padding: 20px; margin-bottom: 20px;'><h2 style='color: $MODE_COLOR; margin-top: 0;'>$SUBJECT</h2><p>$MODE_DESCRIPTION</p></div><div style='background: #f8fafc; padding: 15px; border-radius: 6px; margin: 20px 0;'><h3 style='margin-top: 0; color: #374151;'>📊 Test Details</h3><ul style='color: #6b7280;'><li><strong>Recipient:</strong> $TARGET_EMAIL</li><li><strong>Sent:</strong> $(date -u '+%Y-%m-%d %H:%M:%S UTC')</li><li><strong>Method:</strong> API Gateway → Lambda</li><li><strong>Tracking Mode:</strong> $TRACKING_MODE</li><li><strong>Contact ID:</strong> $CONTACT_ID</li></ul></div><div style='margin: 20px 0;'><h3 style='color: #374151;'>🔗 Test Links</h3><p><a href='https://example.com/test-cta-button' style='color: #2563eb; text-decoration: none;'>Primary CTA Button</a> (will be tracked for clicks)</p><p><a href='https://github.com/sentinel' style='color: #2563eb; text-decoration: none;'>Secondary Link</a> (also tracked)</p><p><a href='mailto:support@thesentinel.site' style='color: #6b7280; text-decoration: none;'>Support Email</a> (not tracked)</p></div><div style='background: #ecfdf5; border: 1px solid #d1fae5; padding: 15px; border-radius: 6px; margin: 20px 0;'><p style='color: #065f46; margin: 0;'><strong>✅ Success!</strong> This demonstrates the <strong>$TRACKING_MODE</strong> tracking method in action.</p></div><hr style='border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;'><div style='text-align: center;'><p style='color: #9ca3af; font-size: 14px; margin: 5px 0;'>Powered by Sentinel Enhanced Tracking System</p><p style='color: #9ca3af; font-size: 12px; margin: 5px 0;'>Tracking Mode: $TRACKING_MODE | Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')</p></div></body></html>",
    "text_body": "$SUBJECT\n\n$MODE_DESCRIPTION\n\n📊 Test Details:\n- Recipient: $TARGET_EMAIL\n- Sent: $(date -u '+%Y-%m-%d %H:%M:%S UTC')\n- Method: API Gateway → Lambda\n- Tracking Mode: $TRACKING_MODE\n- Contact ID: $CONTACT_ID\n\n🔗 Test Links:\n- Primary CTA: https://example.com/test-cta-button (tracked)\n- Secondary Link: https://github.com/sentinel (tracked)\n- Support Email: support@thesentinel.site (not tracked)\n\n✅ Success! This demonstrates the $TRACKING_MODE tracking method in action.\n\n---\nPowered by Sentinel Enhanced Tracking System\nTracking Mode: $TRACKING_MODE | Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')",
    "from_email": "no-reply@thesentinel.site",
    "from_name": "Sentinel Enhanced System",
    "segment_id": "all_active",
    "tracking_mode": "$TRACKING_MODE"
}
EOF
)

    RESPONSE=$(curl -s -w "%{http_code}" -X POST "$API_URL/v1/campaigns" \
        -H "Content-Type: application/json" \
        -d "$CAMPAIGN_PAYLOAD")
    
    HTTP_CODE="${RESPONSE: -3}"
    RESPONSE_BODY="${RESPONSE%???}"
    
    if [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "201" ]]; then
        echo "✅ Campaign created successfully via API!"
        echo "Response: $RESPONSE_BODY"
        API_SUCCESS=true
    else
        echo "❌ API method failed (HTTP $HTTP_CODE)"
        echo "Response: $RESPONSE_BODY"
        API_SUCCESS=false
    fi
else
    echo "⚠️ Step 2: API URL not available, skipping API method"
    API_SUCCESS=false
fi

echo ""

# Step 3: Try direct Lambda method
echo "🔧 Step 3: Trying direct Lambda invocation..."

# Find the create-campaign Lambda
CREATE_LAMBDA=$(aws lambda list-functions \
    --query 'Functions[?contains(FunctionName, `create-campaign`)].FunctionName' \
    --output text \
    --region $AWS_REGION 2>/dev/null || echo "")

if [[ -n "$CREATE_LAMBDA" ]]; then
    echo "Found Lambda: $CREATE_LAMBDA"
    
    # Create payload for direct Lambda invocation
    LAMBDA_PAYLOAD=$(cat <<EOF
{
    "name": "Inline Tracking Email for $TARGET_EMAIL",
    "subject": "� Inline Tracking Test - No External Images",
    "html_body": "<html><body style='font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;'><div style='border: 2px solid #7c3aed; border-radius: 8px; padding: 20px; margin-bottom: 20px;'><h2 style='color: #6d28d9; margin-top: 0;'>📦 Inline Tracking Test</h2><p>This email uses <strong>inline tracking pixels</strong> with no external image requests - guaranteed no security warnings!</p></div><div style='background: #faf5ff; padding: 15px; border-radius: 6px; margin: 20px 0;'><h3 style='margin-top: 0; color: #581c87;'>🔧 Technical Details</h3><ul style='color: #7c2d92;'><li><strong>Method:</strong> Direct Lambda Invocation</li><li><strong>Function:</strong> $CREATE_LAMBDA</li><li><strong>Tracking:</strong> Inline Data URI</li><li><strong>Time:</strong> $(date -u '+%Y-%m-%d %H:%M:%S UTC')</li><li><strong>Contact ID:</strong> $CONTACT_ID</li></ul></div><p><strong>✅ Result:</strong> Zero external requests, maximum compatibility!</p></body></html>",
    "text_body": "📦 Inline Tracking Test\n\nThis email uses inline tracking pixels with no external image requests - guaranteed no security warnings!\n\n🔧 Technical Details:\n- Method: Direct Lambda Invocation\n- Function: $CREATE_LAMBDA\n- Tracking: Inline Data URI\n- Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')\n- Contact ID: $CONTACT_ID\n\n✅ Result: Zero external requests, maximum compatibility!",
    "from_email": "no-reply@thesentinel.site",
    "from_name": "Sentinel Inline System",
    "segment_id": "all_active",
    "tracking_mode": "inline"
}
EOF
)
    
    # Invoke Lambda function
    echo "$LAMBDA_PAYLOAD" > /tmp/lambda_payload.json
    LAMBDA_RESPONSE=$(aws lambda invoke \
        --function-name "$CREATE_LAMBDA" \
        --payload file:///tmp/lambda_payload.json \
        --region $AWS_REGION \
        /tmp/lambda_response.json 2>/dev/null && cat /tmp/lambda_response.json || echo "")
    
    if [[ -n "$LAMBDA_RESPONSE" && "$LAMBDA_RESPONSE" != "null" ]]; then
        echo "✅ Direct Lambda invocation successful!"
        echo "Response: $LAMBDA_RESPONSE"
        
        # Check if the response contains an error
        if echo "$LAMBDA_RESPONSE" | grep -q '"error"'; then
            echo "⚠️ Lambda returned an error - checking response..."
            echo "Payload sent: $(cat /tmp/lambda_payload.json | jq . 2>/dev/null || cat /tmp/lambda_payload.json)"
            LAMBDA_SUCCESS=false
        else
            LAMBDA_SUCCESS=true
        fi
    else
        echo "❌ Direct Lambda invocation failed - no response"
        LAMBDA_SUCCESS=false
    fi
else
    echo "❌ Could not find create-campaign Lambda function"
    LAMBDA_SUCCESS=false
fi

echo ""

# Step 4: Fallback to direct SES
echo "📧 Step 4: Trying direct SES method (fallback)..."

# Create a simpler SES message to avoid CLI quoting issues
SIMPLE_HTML="<html><body><h2>Direct SES Test - $TRACKING_MODE Mode</h2><p>Hello ${TARGET_EMAIL%@*}!</p><p>This email was sent directly through AWS SES using <strong>$TRACKING_MODE</strong> mode.</p><p><strong>Time:</strong> $(date -u '+%Y-%m-%d %H:%M:%S UTC')</p><p><strong>Contact ID:</strong> $CONTACT_ID</p><p>SES is working correctly!</p></body></html>"

SIMPLE_TEXT="Direct SES Test - $TRACKING_MODE Mode

Hello ${TARGET_EMAIL%@*}!

This email was sent directly through AWS SES using $TRACKING_MODE mode.

Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')
Contact ID: $CONTACT_ID

SES is working correctly!"

# Create temporary files for SES message
echo "$SIMPLE_HTML" > /tmp/ses_html.txt
echo "$SIMPLE_TEXT" > /tmp/ses_text.txt

SES_RESPONSE=$(aws ses send-email \
    --source "Sentinel Platform <no-reply@thesentinel.site>" \
    --destination "ToAddresses=$TARGET_EMAIL" \
    --message "Subject={Data='Sentinel Direct SES Test - $TRACKING_MODE'},Body={Html={Data='$(cat /tmp/ses_html.txt)'},Text={Data='$(cat /tmp/ses_text.txt)'}}" \
    --region $AWS_REGION \
    --output json 2>/dev/null || echo "")

if [[ -n "$SES_RESPONSE" ]]; then
    MESSAGE_ID=$(echo "$SES_RESPONSE" | grep -o '"MessageId":[^,]*' | cut -d'"' -f4)
    echo "✅ Direct SES email sent successfully!"
    echo "Message ID: $MESSAGE_ID"
    SES_SUCCESS=true
else
    echo "❌ Direct SES send failed"
    
    # Check SES domain verification status
    echo "🔍 Checking SES domain verification..."
    DOMAIN_STATUS=$(aws ses get-identity-verification-attributes \
        --identities thesentinel.site \
        --region $AWS_REGION \
        --output json 2>/dev/null || echo "")
    
    if [[ -n "$DOMAIN_STATUS" ]]; then
        VERIFICATION_STATUS=$(echo "$DOMAIN_STATUS" | jq -r '.VerificationAttributes."thesentinel.site".VerificationStatus // "Unknown"')
        echo "   Domain status: $VERIFICATION_STATUS"
        
        if [[ "$VERIFICATION_STATUS" != "Success" ]]; then
            echo "   ⚠️ Domain not verified - this may be why SES failed"
            echo "   Run: aws ses get-identity-verification-attributes --identities thesentinel.site --region $AWS_REGION"
        fi
    else
        echo "   ⚠️ Could not check domain status"
    fi
    
    SES_SUCCESS=false
fi

echo ""
echo "=================================="
echo "📊 ENHANCED TRACKING TEST SUMMARY"
echo "=================================="

SUCCESS_COUNT=0
SUCCESS_METHODS=()

if [[ "$API_SUCCESS" == "true" ]]; then
    SUCCESS_METHODS+=("API Gateway")
    ((SUCCESS_COUNT++))
fi

if [[ "$LAMBDA_SUCCESS" == "true" ]]; then
    SUCCESS_METHODS+=("Direct Lambda")
    ((SUCCESS_COUNT++))
fi

if [[ "$SES_SUCCESS" == "true" ]]; then
    SUCCESS_METHODS+=("Direct SES")
    ((SUCCESS_COUNT++))
fi

echo "🎯 Tracking Mode: $TRACKING_MODE"
echo "📧 Target Email: $TARGET_EMAIL"
echo "🆔 Contact ID: $CONTACT_ID"
echo "📈 Success Count: $SUCCESS_COUNT/3 methods"

if [[ $SUCCESS_COUNT -gt 0 ]]; then
    echo ""
    echo "✅ SUCCESS! Email sent via: ${SUCCESS_METHODS[*]}"
    echo "📬 Check $TARGET_EMAIL inbox (including spam folder)"
    echo ""
    echo "🎯 Expected Behavior by Tracking Mode:"
    case "$TRACKING_MODE" in
        "smart")
            echo "   📊 Smart Mode: Minimal warnings, full analytics"
            echo "   🔍 Uses hybrid inline + external pixel approach"
            ;;
        "inline")
            echo "   📦 Inline Mode: Zero security warnings guaranteed"
            echo "   🔍 Uses data URI pixels only (no external requests)"
            ;;
        "external")
            echo "   🖼️  External Mode: May show security warnings"
            echo "   🔍 Uses traditional external image pixels"
            ;;
        "disabled")
            echo "   🚫 Disabled Mode: Clean email, no tracking"
            echo "   🔍 No pixels or analytics (maximum compatibility)"
            ;;
    esac
else
    echo ""
    echo "❌ All methods failed!"
    echo ""
    echo "🔧 Troubleshooting steps:"
    echo "   1. Verify AWS credentials: aws sts get-caller-identity"
    echo "   2. Check SES domain verification:"
    echo "      aws ses get-identity-verification-attributes --identities thesentinel.site --region $AWS_REGION"
    echo "   3. List Lambda functions: aws lambda list-functions --region $AWS_REGION"
    echo "   4. Check DynamoDB tables: aws dynamodb list-tables --region $AWS_REGION"
fi

echo ""
echo "🔍 Verification Commands:"
echo "   aws ses get-send-statistics --region $AWS_REGION"
echo "   aws logs filter-log-events --log-group-name /aws/lambda/sentinel-send-worker"
echo ""
echo "💡 Usage Examples:"
echo "   $0                    # Uses smart mode (recommended)"
echo "   $0 smart             # Smart hybrid tracking"  
echo "   $0 inline            # Inline data URI (no warnings)"
echo "   $0 external          # Traditional external pixel"
echo "   $0 disabled          # Clean email (no tracking)"
echo ""
echo "🎯 Done! Enhanced tracking test completed for mode: $TRACKING_MODE 🚀"

# Cleanup temporary files
rm -f /tmp/lambda_payload.json /tmp/lambda_response.json /tmp/ses_html.txt /tmp/ses_text.txt 2>/dev/null || true