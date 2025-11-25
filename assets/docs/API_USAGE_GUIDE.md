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

### Update your account info (Name, timezone)

```bash
curl -X POST https://api.thesentinel.site/v1/auth/update \
  -H "X-API-Key: YOUR_CURRENT_API_KEY_HERE"
```

**Request Body:**
```json
{
  "name": "New Name",
  "timezone": "America/New_York"
}
```
- Both fields are optional; only include the ones you want to update.
- If `timezone` is omitted, it remains unchanged. Default is `"UTC"` for new users.

**Response:**
```json
{
  "message": "User updated successfully",
  "user": {
    "id": "user-id-here",
    "name": "New Name",
    "email": "your.email@example.com",
    "api_key": "sk_your-api-key-here",
    "status": "active",
    "timezone": "America/New_York",
    "updated_at": 1763614000
  }
}
```

---


## 🤖 Generate Email Content with AI (Gemini Lambda)

### Endpoint
`POST https://api.thesentinel.site/v1/generate-email`

### Headers
- `Content-Type: application/json`
- `X-API-Key: YOUR_API_KEY_HERE`

### Request Body
```
{
  "tone": "Formal",
  "finalGoal": "Announce new feature",
  "audiences": ["Developers", "Managers"],
  "keyPoints": "Feature X is live\nImproves performance\nEasy to use",
  "links": [{"url": "https://docs.example.com", "text": "Documentation"}]
}
```

### Response
```
{
  "subject": "Announce new feature for Developers, Managers",
  "content": "<h2>Announce new feature</h2>..." // HTML string
}
```

**Note:** This endpoint is powered by a Python Lambda using Google Gemini AI. The API key is securely managed via AWS Secrets Manager.

---

## 🧪 A/B Testing for Email Campaigns

A/B testing allows you to test multiple email variations (A, B, C) to determine which performs best. The system automatically tracks performance metrics and can select a winner based on engagement.

### Create an A/B Test Campaign

#### Step 1: Generate Email Variations

Generate 3 email variations with different tones using AI:

```bash
curl -X POST https://api.thesentinel.site/v1/generate-email \\\n  -H \"Content-Type: application/json\" \\\n  -H \"X-API-Key: YOUR_API_KEY_HERE\" \\\n  -d '{\n    \"tone\": \"Professional,Friendly,Persuasive\",\n    \"finalGoal\": \"Promote new product launch\",\n    \"audiences\": [\"Customers\", \"Prospects\"],\n    \"keyPoints\": \"New features\\nLimited time offer\\nFree trial available\",\n    \"links\": [{\"url\": \"https://product.example.com\", \"text\": \"Learn More\"}]\n  }'
```

**Response:**
```json
[
  {
    \"subject\": \"Introducing Our Latest Innovation\",
    \"content\": \"<h2>Professional tone email...</h2>\"
  },
  {
    \"subject\": \"Check Out What We've Built for You!\",
    \"content\": \"<h2>Friendly tone email...</h2>\"
  },
  {
    \"subject\": \"Don't Miss This Limited Opportunity\",
    \"content\": \"<h2>Persuasive tone email...</h2>\"
  }
]
```

**Note:** When `tone` contains comma-separated values, the API generates multiple variations (up to 3).

#### Step 2: Create A/B Test Campaign

```bash
curl -X POST https://api.thesentinel.site/v1/campaigns \\\n  -H \"Content-Type: application/json\" \\\n  -H \"X-API-Key: YOUR_API_KEY_HERE\" \\\n  -d '{\n    \"name\": \"Product Launch A/B Test\",\n    \"type\": \"AB\",\n    \"delivery_type\": \"SEG\",\n    \"segment_id\": \"YOUR_SEGMENT_ID\",\n    \"from_email\": \"marketing@yourcompany.com\",\n    \"from_name\": \"Marketing Team\",\n    \"ab_test_config\": {\n      \"variations\": [\n        {\n          \"id\": \"A\",\n          \"subject\": \"Introducing Our Latest Innovation\",\n          \"html_body\": \"<h2>Professional tone email...</h2>\"\n        },\n        {\n          \"id\": \"B\",\n          \"subject\": \"Check Out What We'\''ve Built for You!\",\n          \"html_body\": \"<h2>Friendly tone email...</h2>\"\n        },\n        {\n          \"id\": \"C\",\n          \"subject\": \"Don'\''t Miss This Limited Opportunity\",\n          \"html_body\": \"<h2>Persuasive tone email...</h2>\"\n        }\n      ],\n      \"test_duration_hours\": 24,\n      \"winner_criteria\": \"engagement_rate\"\n    }\n  }'
```

**Campaign Type for A/B Testing:**
- `\"AB\"` - A/B Test campaign (requires `ab_test_config`)

**A/B Test Configuration:**
- `variations` - Array of 2-3 email variations (each with `id`, `subject`, `html_body`)
- `test_duration_hours` - How long to run the test before selecting a winner (optional, default: 24)
- `winner_criteria` - Metric to determine winner: `\"open_rate\"`, `\"click_rate\"`, or `\"engagement_rate\"` (optional, default: \"engagement_rate\")

**Response:**
```json
{
  \"message\": \"Campaign created and scheduled successfully\",
  \"campaign\": {
    \"id\": \"campaign-id-here\",
    \"name\": \"Product Launch A/B Test\",
    \"type\": \"AB\",
    \"status\": \"scheduled\",
    \"recipient_count\": 300,
    \"ab_test_config\": {
      \"variations\": [
        {\"id\": \"A\", \"subject\": \"Introducing Our Latest Innovation\"},
        {\"id\": \"B\", \"subject\": \"Check Out What We've Built for You!\"},
        {\"id\": \"C\", \"subject\": \"Don't Miss This Limited Opportunity\"}
      ],
      \"test_duration_hours\": 24,
      \"winner_criteria\": \"engagement_rate\"
    }
  }
}
```

### View A/B Test Analytics

#### Get Overall Campaign Analytics
```bash
curl -H \"X-API-Key: YOUR_API_KEY_HERE\" \\\n  \"https://api.thesentinel.site/v1/campaigns/YOUR_CAMPAIGN_ID/events\"
```

#### Get Analytics for Specific Variation
```bash
curl -H \"X-API-Key: YOUR_API_KEY_HERE\" \\\n  \"https://api.thesentinel.site/v1/campaigns/YOUR_CAMPAIGN_ID/events?variation_id=A\"
```

**Query Parameters:**
- `variation_id` - Filter events by variation (`A`, `B`, or `C`)
- `from_epoch` - Unix timestamp to filter events from (optional)
- `to_epoch` - Unix timestamp to filter events until (optional)
- `limit` - Maximum number of events to return (default: 1000)

**Response with Variation Filtering:**
```json
{
  \"events\": [
    {
      \"event_type\": \"open\",
      \"timestamp\": 1700050000,
      \"variation_id\": \"A\",
      \"recipient_email\": \"user@example.com\"
    }
  ],
  \"summary\": {
    \"total_events\": 45,
    \"unique_opens\": 30,
    \"unique_clicks\": 12,
    \"event_counts\": {
      \"open\": 35,
      \"click\": 10
    },
    \"campaign_id\": \"campaign-id-here\",
    \"variation_id\": \"A\"
  }
}
```

### A/B Test Winner Selection

The system automatically analyzes A/B test performance after the test duration and selects a winner based on the specified criteria.

**Winner Criteria Options:**
- `\"open_rate\"` - Highest percentage of recipients who opened the email
- `\"click_rate\"` - Highest percentage of recipients who clicked links
- `\"engagement_rate\"` - Combined metric of opens and clicks (default)

**Automatic Winner Selection:**
After the test duration expires, the `ab_test_analyzer` Lambda automatically:
1. Analyzes performance metrics for each variation
2. Selects the winning variation based on the criteria
3. Updates the campaign with the winner ID

**Check Winner Status:**
```bash
curl -H \"X-API-Key: YOUR_API_KEY_HERE\" \\\n  \"https://api.thesentinel.site/v1/campaigns/YOUR_CAMPAIGN_ID\"
```

**Response with Winner:**
```json
{
  \"campaign\": {
    \"id\": \"campaign-id-here\",
    \"name\": \"Product Launch A/B Test\",
    \"type\": \"AB\",
    \"status\": \"completed\",
    \"ab_test_config\": {
      \"variations\": [...],
      \"winner_id\": \"B\",
      \"winner_selected_at\": 1700136400
    }
  }
}
```

### A/B Test Best Practices

1. **Segment Size**: Ensure your segment has at least 100 recipients for statistically significant results
2. **Test Duration**: Run tests for at least 24 hours to capture different time zones and user behaviors
3. **Single Variable**: Test one element at a time (subject line, tone, or content) for clearer insights
4. **Variation Distribution**: Recipients are automatically distributed evenly across variations
5. **Winner Criteria**: Choose criteria based on your campaign goal:
   - Use `open_rate` for subject line testing
   - Use `click_rate` for CTA and content testing
   - Use `engagement_rate` for overall performance

---

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

#### Immediate Campaign with Segment
```bash
curl -X POST https://api.thesentinel.site/v1/campaigns \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "name": "My First Email Test",
    "type": "I",
    "delivery_type": "SEG",
    "subject": "Hello from Sentinel! 👋",
    "html_body": "<h1>Welcome!</h1><p>This is a test email from Sentinel.</p><p>Click <a href=\"https://example.com\">here</a> to visit our website.</p>",
    "segment_id": "YOUR_SEGMENT_ID_HERE",
    "from_email": "hello@yourcompany.com",
    "from_name": "Your Company"
  }'
```

#### Scheduled Campaign with Segment
```bash
curl -X POST https://api.thesentinel.site/v1/campaigns \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "name": "Scheduled Newsletter",
    "type": "S",
    "delivery_type": "SEG", 
    "subject": "Weekly Newsletter 📰",
    "html_body": "<h1>This Week'\''s Updates</h1><p>Here are the latest updates...</p>",
    "segment_id": "YOUR_SEGMENT_ID_HERE",
    "schedule_at": 1735128000,
    "from_email": "newsletter@yourcompany.com",
    "from_name": "Your Company Newsletter"
  }'
```

#### Individual Email Campaign
```bash
curl -X POST https://api.thesentinel.site/v1/campaigns \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "name": "Personal Email",
    "type": "I",
    "delivery_type": "IND",
    "subject": "Personal Message 💌",
    "html_body": "<h1>Hello!</h1><p>This is a personal message just for you.</p>",
    "recipient_email": "friend@example.com",
    "from_email": "you@yourcompany.com",
    "from_name": "Your Name"
  }'
```

#### Campaign with Direct Email List
```bash
curl -X POST https://api.thesentinel.site/v1/campaigns \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "name": "Direct Email Campaign",
    "type": "I",
    "delivery_type": "SEG",
    "subject": "Special Announcement 🎉",
    "html_body": "<h1>Special Offer!</h1><p>Limited time offer just for you.</p>",
    "emails": ["friend1@example.com", "friend2@example.com"],
    "from_email": "offers@yourcompany.com",
    "from_name": "Special Offers Team"
  }'
```

**Campaign Types:**
- `"I"` - Immediate execution
- `"S"` - Scheduled execution (requires `schedule_at` as Unix timestamp)
- `"AB"` - A/B Test campaign (requires `ab_test_config`)

**Delivery Types:**
- `"IND"` - Individual email (requires `recipient_email`)
- `"SEG"` - Segment-based (requires `segment_id` or `emails` array)

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

### View Campaign Analytics & Events - Private Access Only

#### Get All Campaign Events
```bash
curl -H "X-API-Key: YOUR_API_KEY_HERE" \
  "https://api.thesentinel.site/v1/campaigns/YOUR_CAMPAIGN_ID/events"
```

#### Get Events with Time Range Filtering
```bash
curl -H "X-API-Key: YOUR_API_KEY_HERE" \
  "https://api.thesentinel.site/v1/campaigns/YOUR_CAMPAIGN_ID/events?from_epoch=1700000000&to_epoch=1700086400&limit=1000"
```

**Enhanced Response Example:**
```json
{
  "events": [
    {
      "event_type": "open",
      "timestamp": 1700050000,
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)...",
      "recipient_email": "user@example.com"
    }
  ],
  "summary": {
    "total_events": 240,
    "event_counts": {
      "open": 150,
      "click": 75,
      "bounce": 12,
      "unsubscribe": 3
    },
    "event_types_breakdown": [
      {
        "event_type": "open",
        "count": 150,
        "percentage": 62.5
      },
      {
        "event_type": "click",
        "count": 75,
        "percentage": 31.25
      }
    ],
    "campaign_id": "campaign-id-here",
    "campaign_name": "My Campaign",
    "time_range": {
      "from_epoch": "1700000000",
      "to_epoch": "1700086400"
    }
  },
  "distributions": {
    "os_distribution": [
      {"name": "iOS", "value": 45},
      {"name": "Android", "value": 30},
      {"name": "Windows 10", "value": 25}
    ],
    "device_distribution": [
      {"name": "iPhone", "value": 40},
      {"name": "Desktop", "value": 35},
      {"name": "Android Phone", "value": 25}
    ],
    "browser_distribution": [
      {"name": "Chrome", "value": 60},
      {"name": "Safari", "value": 30},
      {"name": "Firefox", "value": 10}
    ],
    "ip_distribution": [
      {"name": "192.168.1.1", "value": 15},
      {"name": "10.0.0.1", "value": 12},
      {"name": "Other", "value": 73}
    ]
  },
  "has_more": false
}
```

**Query Parameters:**
- `from_epoch` - Unix timestamp to filter events from (optional)
- `to_epoch` - Unix timestamp to filter events until (optional)
- `limit` - Maximum number of events to return (default: 1000, max: 1000)

**Distribution Data:**
The API now provides ready-to-use analytics data for dashboard charts:
- **OS Distribution** - Operating system breakdown (iOS, Android, Windows, etc.)
- **Device Distribution** - Device type analysis (iPhone, Desktop, Android Phone, etc.)
- **Browser Distribution** - Browser usage statistics (Chrome, Safari, Firefox, etc.)
- **IP Distribution** - Geographic/network analysis by IP address

**Note:** Campaign events are only accessible to the campaign owner through this authenticated endpoint for privacy and security.

---

## 📊 Advanced Analytics Features

The Campaign Events API provides comprehensive analytics data perfect for building dashboards and understanding campaign performance.

### Event Types Tracked
- **open** - Email opened by recipient
- **click** - Link clicked within email
- **bounce** - Email delivery failed
- **unsubscribe** - Recipient unsubscribed
- **spam** - Email marked as spam
- **delivered** - Email successfully delivered

### Distribution Analytics

#### 1. Operating System Distribution
See which operating systems your audience uses:
```json
"os_distribution": [
  {"name": "iOS", "value": 45},
  {"name": "Android", "value": 30},
  {"name": "Windows 10", "value": 25},
  {"name": "macOS", "value": 20},
  {"name": "Other", "value": 10}
]
```

#### 2. Device Type Distribution
Understand device preferences:
```json
"device_distribution": [
  {"name": "iPhone", "value": 40},
  {"name": "Desktop", "value": 35},
  {"name": "Android Phone", "value": 25},
  {"name": "iPad", "value": 15},
  {"name": "Android Tablet", "value": 5}
]
```

#### 3. Browser Distribution
Track browser usage patterns:
```json
"browser_distribution": [
  {"name": "Chrome", "value": 60},
  {"name": "Safari", "value": 30},
  {"name": "Firefox", "value": 10},
  {"name": "Microsoft Edge", "value": 8},
  {"name": "Other", "value": 2}
]
```

#### 4. Geographic Analysis (IP Distribution)
Monitor engagement by location/network:
```json
"ip_distribution": [
  {"name": "192.168.1.1", "value": 15},
  {"name": "10.0.0.1", "value": 12},
  {"name": "203.0.113.1", "value": 8},
  {"name": "Other", "value": 65}
]
```

### Time-Based Filtering

#### Filter by Date Range
```bash
# Get events from the last 7 days
FROM_DATE=$(date -d '7 days ago' +%s)
TO_DATE=$(date +%s)

curl -H "X-API-Key: YOUR_API_KEY_HERE" \
  "https://api.thesentinel.site/v1/campaigns/YOUR_CAMPAIGN_ID/events?from_epoch=${FROM_DATE}&to_epoch=${TO_DATE}"
```

#### Filter by Specific Time Period
```bash
# Get events from December 1-31, 2024
curl -H "X-API-Key: YOUR_API_KEY_HERE" \
  "https://api.thesentinel.site/v1/campaigns/YOUR_CAMPAIGN_ID/events?from_epoch=1701388800&to_epoch=1704067199"
```

### Event Summary Statistics

The API provides detailed breakdowns:
```json
"event_types_breakdown": [
  {
    "event_type": "open",
    "count": 150,
    "percentage": 62.5
  },
  {
    "event_type": "click", 
    "count": 75,
    "percentage": 31.25
  },
  {
    "event_type": "bounce",
    "count": 12, 
    "percentage": 5.0
  }
]
```

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

### Refresh Segment Counts
Recalculate the number of contacts in all your segments. Useful if counts get out of sync.

```bash
curl -X POST https://api.thesentinel.site/v1/segments/refresh-counts \
  -H "X-API-Key: YOUR_API_KEY_HERE"
```

**Response:**
```json
{
  "message": "Updated contact counts for 5 segments",
  "segments": [
    {
      "id": "segment-id-1",
      "name": "Newsletter Subscribers",
      "contact_count": 150
    },
    {
      "id": "segment-id-2",
      "name": "Test Group",
      "contact_count": 5
    }
  ]
}
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
- `POST /v1/campaigns` - Create campaign (supports types: I, S, AB)
- `GET /v1/campaigns/{id}` - Get campaign
- `PUT /v1/campaigns/{id}` - Update campaign
- `DELETE /v1/campaigns/{id}` - Delete campaign
- `GET /v1/campaigns/{id}/events` - Get campaign analytics & events
- `GET /v1/campaigns/{id}/events?variation_id={A|B|C}` - Get A/B test variation analytics

### AI & A/B Testing Endpoints
- `POST /v1/generate-email` - Generate email content with AI
  - Single tone: Returns one email
  - Multiple tones (comma-separated): Returns array of variations for A/B testing

### Segment Endpoints
- `GET /v1/segments` - List segments
- `POST /v1/segments` - Create segment
- `GET /v1/segments/{id}` - Get segment
- `PUT /v1/segments/{id}` - Update segment
- `DELETE /v1/segments/{id}` - Delete segment
- `GET /v1/segments/{id}/emails` - Get segment emails
- `POST /v1/segments/{id}/emails` - Add emails
- `DELETE /v1/segments/{id}/emails` - Remove emails
- `POST /v1/segments/refresh-counts` - Refresh segment contact counts

### Tracking & Events Endpoints
- `GET /track/open/{campaign_id}/{recipient_id}.png` - Track email open
- `GET /track/click/{tracking_id}` - Track link click
- `GET /unsubscribe/{token}` - Unsubscribe link

Replace `YOUR_API_KEY_HERE`, `YOUR_SEGMENT_ID_HERE`, and `YOUR_CAMPAIGN_ID` with your actual values from the API responses.