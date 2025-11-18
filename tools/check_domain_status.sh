#!/bin/bash

# Check thesentinel.site verification status
echo "🔍 Checking thesentinel.site verification status..."

aws ses get-identity-verification-attributes --identities thesentinel.site --region us-east-1 --output json | jq -r '
if .VerificationAttributes."thesentinel.site".VerificationStatus == "Success" then
  "✅ VERIFIED! Domain thesentinel.site is ready for sending emails"
elif .VerificationAttributes."thesentinel.site".VerificationStatus == "Pending" then  
  "⏳ PENDING: DNS record added but still propagating. Check again in 15-30 minutes."
else
  "❌ NOT VERIFIED: Add the DNS TXT record and wait for propagation"
end'

echo ""
echo "📧 Once verified, update your Terraform configuration:"
echo 'SES_FROM_ADDRESS = "noreply@thesentinel.site"'