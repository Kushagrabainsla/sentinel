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

## 📊 Check Email Performance

### View Campaign Events
```bash
curl -H "X-API-Key: YOUR_API_KEY_HERE" \
  "https://api.thesentinel.site/v1/campaigns/YOUR_CAMPAIGN_ID/events"
```

### List All Campaigns
```bash
curl -H "X-API-Key: YOUR_API_KEY_HERE" \
  https://api.thesentinel.site/v1/campaigns
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

## 📚 Need More Help?

- **List all segments:** `GET /v1/segments`
- **Get user info:** `GET /v1/auth/me`
- **Delete a segment:** `DELETE /v1/segments/{id}`
- **View campaign details:** `GET /v1/campaigns/{id}`

Replace `YOUR_API_KEY_HERE` and `YOUR_SEGMENT_ID_HERE` with your actual values from the responses above.