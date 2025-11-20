# Sentinel API Usage Guide

A simple guide to get started with user creation and email campaigns.

## 🔗 API Base URL

```
https://api.thesentinel.site/v1
```

## 📝 1. Create a User Account

### Register a New User

```bash
curl -X POST https://api.thesentinel.site/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Your Name",
    "email": "your.email@example.com",
    "password": "YourSecurePassword123!"
  }'
```

**Response:**
```json
{
  "message": "User created successfully",
  "user": {
    "id": "user-id-here",
    "name": "Your Name",
    "email": "your.email@example.com",
    "api_key": "sk_your-api-key-here",
    "status": "active",
    "created_at": 1763614000
  }
}
```

**⚠️ Important:** Save your `api_key` - you'll need it for all future API calls!

### Login (Existing Users)

```bash
curl -X POST https://api.thesentinel.site/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your.email@example.com",
    "password": "YourSecurePassword123!"
  }'
```

**Response:**
```json
{
  "message": "Authentication successful",
  "user": {
    "id": "user-id-here",
    "name": "Your Name",
    "email": "your.email@example.com",
    "api_key": "sk_your-api-key-here",
    "status": "active"
  }
}
```

### Get Your Account Info

```bash
curl -H "X-API-Key: YOUR_API_KEY_HERE" \
  https://api.thesentinel.site/v1/auth/me
```

### Regenerate Your API Key

```bash
curl -X POST https://api.thesentinel.site/v1/auth/regenerate-key \
  -H "X-API-Key: YOUR_CURRENT_API_KEY_HERE"
```

**Response:**
```json
{
  "message": "API key regenerated successfully",
  "api_key": "sk_your-new-api-key-here"
}
```

---

## 📧 2. Test Email Sending

### Step 1: Create an Email Segment

Create a list of email recipients:

```bash
curl -X POST https://api.thesentinel.site/v1/segments \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "name": "Test Recipients",
    "description": "My first email test",
    "emails": [
      "test1@example.com",
      "test2@example.com",
      "your.email@example.com"
    ]
  }'
```

**Response:**
```json
{
  "message": "Segment created successfully",
  "segment": {
    "id": "segment-id-here",
    "name": "Test Recipients",
    "contact_count": 3,
    "status": "active"
  }
}
```

### Step 2: Create an Email Campaign

#### Immediate Campaign
```bash
curl -X POST https://api.thesentinel.site/v1/campaigns \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "name": "My First Email Test",
    "subject": "Hello from Sentinel! 👋",
    "content": "<h1>Welcome!</h1><p>This is a test email from Sentinel.</p><p>Click <a href=\"https://example.com\">here</a> to visit our website.</p>",
    "segment_id": "YOUR_SEGMENT_ID_HERE",
    "schedule_type": "immediate"
  }'
```

#### Scheduled Campaign
```bash
curl -X POST https://api.thesentinel.site/v1/campaigns \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "name": "Scheduled Newsletter",
    "subject": "Weekly Newsletter 📰",
    "content": "<h1>This Week'\''s Updates</h1><p>Here are the latest updates...</p>",
    "segment_id": "YOUR_SEGMENT_ID_HERE",
    "schedule_type": "scheduled",
    "scheduled_time": "2024-12-25T10:00:00Z"
  }'
```

#### Campaign with Email List (instead of segment)
```bash
curl -X POST https://api.thesentinel.site/v1/campaigns \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "name": "Direct Email Campaign",
    "subject": "Special Announcement 🎉",
    "content": "<h1>Special Offer!</h1><p>Limited time offer just for you.</p>",
    "emails": ["friend1@example.com", "friend2@example.com"],
    "schedule_type": "immediate"
  }'
```

**Response:**
```json
{
  "message": "Campaign created and scheduled successfully",
  "campaign": {
    "id": "campaign-id-here",
    "name": "My First Email Test",
    "status": "scheduled",
    "recipient_count": 3,
    "schedule_type": "immediate"
  }
}
```

### Step 3: Check Campaign Status

```bash
curl -H "X-API-Key: YOUR_API_KEY_HERE" \
  https://api.thesentinel.site/v1/campaigns
```


---

## 📊 Campaign Management

### List All Campaigns
```bash
curl -H "X-API-Key: YOUR_API_KEY_HERE" \
  https://api.thesentinel.site/v1/campaigns
```

### Get Campaign Details
```bash
curl -H "X-API-Key: YOUR_API_KEY_HERE" \
  "https://api.thesentinel.site/v1/campaigns/YOUR_CAMPAIGN_ID"
```

### Update a Campaign
```bash
curl -X PUT https://api.thesentinel.site/v1/campaigns/YOUR_CAMPAIGN_ID \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "name": "Updated Campaign Name",
    "subject": "Updated Subject Line"
  }'
```

### Delete a Campaign
```bash
curl -X DELETE https://api.thesentinel.site/v1/campaigns/YOUR_CAMPAIGN_ID \
  -H "X-API-Key: YOUR_API_KEY_HERE"
```

### View Campaign Events (Opens, Clicks, etc.) - Private Access Only
```bash
curl -H "X-API-Key: YOUR_API_KEY_HERE" \
  "https://api.thesentinel.site/v1/campaigns/YOUR_CAMPAIGN_ID/events"
```

**Note:** Campaign events are only accessible to the campaign owner through this authenticated endpoint for privacy and security.

---

## 📋 Segment Management

### List All Segments
```bash
curl -H "X-API-Key: YOUR_API_KEY_HERE" \
  https://api.thesentinel.site/v1/segments
```

### Get Segment Details
```bash
curl -H "X-API-Key: YOUR_API_KEY_HERE" \
  "https://api.thesentinel.site/v1/segments/YOUR_SEGMENT_ID"
```

### Update a Segment
```bash
curl -X PUT https://api.thesentinel.site/v1/segments/YOUR_SEGMENT_ID \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "name": "Updated Segment Name",
    "description": "Updated description"
  }'
```

### Add Emails to Segment
```bash
curl -X POST https://api.thesentinel.site/v1/segments/YOUR_SEGMENT_ID/emails \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "emails": ["new1@example.com", "new2@example.com"]
  }'
```

### Remove Emails from Segment
```bash
curl -X DELETE https://api.thesentinel.site/v1/segments/YOUR_SEGMENT_ID/emails \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "emails": ["remove1@example.com", "remove2@example.com"]
  }'
```

### Get Segment Emails
```bash
curl -H "X-API-Key: YOUR_API_KEY_HERE" \
  "https://api.thesentinel.site/v1/segments/YOUR_SEGMENT_ID/emails"
```

### Delete a Segment
```bash
curl -X DELETE https://api.thesentinel.site/v1/segments/YOUR_SEGMENT_ID \
  -H "X-API-Key: YOUR_API_KEY_HERE"
```

---

## 🔧 Common Issues & Solutions

### Issue: "Authentication failed"
**Solution:** Make sure you're using the correct API key in the `X-API-Key` header.

### Issue: "Segment not found" 
**Solution:** Verify the segment ID exists by listing segments first:
```bash
curl -H "X-API-Key: YOUR_API_KEY_HERE" \
  https://api.thesentinel.site/v1/segments
```

### Issue: Emails not sending
**Solution:** Check campaign status - it should be "completed". If "failed", check the campaign events for error details.

---

## 🔗 Public Tracking URLs

These URLs don't require authentication and are used for email tracking:

- **Email opens:** `GET /track/open/{tracking_id}`
- **Link clicks:** `GET /track/click/{tracking_id}`
- **Unsubscribe:** `GET /unsubscribe/{tracking_id}`

---

## 📚 Quick Reference

### Authentication Endpoints
- `POST /v1/auth/register` - Create account
- `POST /v1/auth/login` - Login 
- `GET /v1/auth/me` - Get account info
- `POST /v1/auth/regenerate-key` - Regenerate API key

### Campaign Endpoints
- `GET /v1/campaigns` - List campaigns
- `POST /v1/campaigns` - Create campaign
- `GET /v1/campaigns/{id}` - Get campaign
- `PUT /v1/campaigns/{id}` - Update campaign
- `DELETE /v1/campaigns/{id}` - Delete campaign
- `GET /v1/campaigns/{id}/events` - Get campaign events

### Segment Endpoints
- `GET /v1/segments` - List segments
- `POST /v1/segments` - Create segment
- `GET /v1/segments/{id}` - Get segment
- `PUT /v1/segments/{id}` - Update segment
- `DELETE /v1/segments/{id}` - Delete segment
- `GET /v1/segments/{id}/emails` - Get segment emails
- `POST /v1/segments/{id}/emails` - Add emails
- `DELETE /v1/segments/{id}/emails` - Remove emails

Replace `YOUR_API_KEY_HERE`, `YOUR_SEGMENT_ID_HERE`, and `YOUR_CAMPAIGN_ID` with your actual values from the API responses.