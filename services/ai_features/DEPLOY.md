# AI Features Deployment Guide

## Required Environment Variables

Before deploying, you need to set these environment variables:

1. **GEMINI_API_KEY** - Your Google Gemini API key
2. **DYNAMODB_CAMPAIGNS_TABLE** - DynamoDB campaigns table name
3. **DYNAMODB_EVENTS_TABLE** - DynamoDB events table name

## Deployment Command

```bash
cd services/ai_features

export GEMINI_API_KEY="your-gemini-api-key-here"
export DYNAMODB_CAMPAIGNS_TABLE="your-campaigns-table-name"
export DYNAMODB_EVENTS_TABLE="your-events-table-name"

sls deploy --verbose
```

## Finding Your Table Names

Check your Terraform outputs or AWS Console:
```bash
cd infra
terraform output
```

Or check AWS DynamoDB console for tables starting with `sentinel-`.
