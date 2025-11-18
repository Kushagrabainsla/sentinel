# Dual-Path Campaign Scheduling Architecture

## 🎯 Overview

Sentinel uses an intelligent **dual-path scheduling system** that optimizes campaign execution based on timing:

- **⚡ Immediate Path**: For campaigns scheduled ≤1 minute → Direct Lambda invocation
- **📅 Scheduled Path**: For campaigns scheduled >1 minute → EventBridge Scheduler

## 🏗️ Architecture Diagram

```
┌─────────────────┐
│ POST /campaigns │
│ {schedule_at}   │
└─────────┬───────┘
          │
    ┌─────▼─────┐
    │ Decision  │
    │ Logic     │
    └─────┬─────┘
          │
     ≤1 min vs >1 min?
          │
    ┌─────▼─────┐────────────────┐
    │           │                │
┌───▼───┐   ┌───▼────┐      ┌────▼────┐
│⚡ NOW │   │📅 LATER │      │🔄 SKIP  │
│       │   │        │      │         │
│Direct │   │EventBr │      │Invalid  │
│Lambda │   │Schedul │      │Time     │
│Invoke │   │        │      │         │
└───┬───┘   └───┬────┘      └─────────┘
    │           │
    └─────┬─────┘
          │
    ┌─────▼─────┐
    │start_camp │
    │  Lambda   │
    └─────┬─────┘
          │
    ┌─────▼─────┐
    │    SQS    │
    │send-queue │
    └─────┬─────┘
          │
    ┌─────▼─────┐
    │send_worker│
    │  Lambda   │
    └─────┬─────┘
          │
    ┌─────▼─────┐
    │    SES    │
    │Email Send │
    └───────────┘
```

## 📊 Decision Logic

### **When `schedule_at` is provided:**

```python
schedule_dt = datetime.fromisoformat(schedule_at.replace('Z', '+00:00'))
now = datetime.now(timezone.utc)
time_diff = (schedule_dt - now).total_seconds()

if time_diff <= 60:  # ≤1 minute
    # ⚡ IMMEDIATE PATH
    trigger_immediate_campaign(campaign_id)
    state = "sending"
    execution_path = "immediate"
else:
    # 📅 SCHEDULED PATH  
    create_scheduler_rule(campaign_id, schedule_at)
    state = "scheduled"
    execution_path = "scheduled"
```

### **When `schedule_at` is NOT provided:**
- Defaults to `datetime.now(timezone.utc).isoformat()`
- Always uses **⚡ Immediate Path**

## 🚀 Execution Paths Explained

### ⚡ **Immediate Path** (≤1 minute)

**Trigger:** Campaign scheduled within 1 minute of creation

**Flow:**
```
create_campaign Lambda
    ↓
Direct invoke start_campaign Lambda (async)
    ↓
start_campaign processes contacts
    ↓
Creates recipient records in DynamoDB
    ↓
Sends messages to SQS send-queue
    ↓
send_worker Lambda processes SQS messages
    ↓
Sends emails via SES
```

**Benefits:**
- ✅ **Zero latency** - no scheduler overhead
- ✅ **Immediate execution** - starts within seconds
- ✅ **Simpler debugging** - direct Lambda logs
- ✅ **Cost efficient** - no EventBridge charges

**Response:**
```json
{
  "campaign_id": "uuid-123",
  "state": "sending",
  "schedule_at": "2025-11-18T15:30:00Z",
  "execution_path": "immediate",
  "triggered": true
}
```

### 📅 **Scheduled Path** (>1 minute)

**Trigger:** Campaign scheduled more than 1 minute in the future

**Flow:**
```
create_campaign Lambda
    ↓
Creates EventBridge Scheduler rule
    ↓
Rule waits until scheduled time
    ↓
EventBridge invokes start_campaign Lambda
    ↓
[Same as immediate path from here]
```

**Benefits:**
- ✅ **Precise timing** - executes exactly at scheduled time
- ✅ **Reliable scheduling** - AWS-managed timing
- ✅ **Auto-cleanup** - rules delete after execution
- ✅ **Scalable** - handles thousands of scheduled campaigns

**Response:**
```json
{
  "campaign_id": "uuid-456", 
  "state": "scheduled",
  "schedule_at": "2025-11-18T17:30:00Z",
  "execution_path": "scheduled",
  "auto_scheduler": true
}
```

## 🔧 Configuration

### **Environment Variables (create_campaign Lambda)**
```bash
START_CAMPAIGN_LAMBDA_ARN="arn:aws:lambda:us-east-1:123:function:sentinel-start-campaign"
EVENTBRIDGE_ROLE_ARN="arn:aws:iam::123:role/sentinel-scheduler-invoke"
```

### **IAM Permissions Required**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:*:*:function:sentinel-start-campaign"
    },
    {
      "Effect": "Allow", 
      "Action": [
        "scheduler:CreateSchedule",
        "scheduler:DeleteSchedule"
      ],
      "Resource": "*"
    }
  ]
}
```

## 📝 Usage Examples

### **Immediate Campaign (No schedule_at)**
```bash
curl -X POST /v1/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Flash Sale",
    "template_id": "promo-template",
    "segment_id": "vip-customers"
  }'
```
→ **Result:** Executes immediately via direct Lambda invoke

### **Immediate Campaign (schedule_at = now)**
```bash
curl -X POST /v1/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Breaking News",
    "template_id": "news-template", 
    "segment_id": "all-subscribers",
    "schedule_at": "2025-11-18T15:31:00Z"
  }'
```
→ **Result:** If current time is 15:30:30, executes immediately (30 seconds ≤ 1 minute)

### **Scheduled Campaign (schedule_at = future)**
```bash
curl -X POST /v1/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Weekly Newsletter",
    "template_id": "newsletter-template",
    "segment_id": "all-active",
    "schedule_at": "2025-11-19T09:00:00Z"
  }'
```
→ **Result:** Creates EventBridge Scheduler rule for tomorrow 9 AM

## 🎯 Benefits of Dual-Path Approach

| Aspect | Immediate Path | Scheduled Path | 
|--------|----------------|----------------|
| **Latency** | ~2-5 seconds | Exact scheduled time |
| **Cost** | Lower (no EventBridge) | Slightly higher |
| **Complexity** | Simpler | More moving parts |
| **Use Case** | Urgent/immediate | Marketing campaigns |
| **Debugging** | Direct logs | Distributed logs |
| **Scalability** | Limited by Lambda concurrency | AWS-managed scheduling |

## 🛠️ Monitoring & Debugging

### **CloudWatch Metrics to Watch**
- `Lambda Duration` (create_campaign, start_campaign)
- `EventBridge ScheduledRules` (scheduled campaigns)
- `SQS MessagesSent` (campaign processing)
- `Lambda Errors` (failed executions)

### **Log Analysis**
```bash
# Immediate path logs
aws logs filter-log-events --log-group-name /aws/lambda/sentinel-create-campaign \
  --filter-pattern "⚡ Immediate execution"

# Scheduled path logs  
aws logs filter-log-events --log-group-name /aws/lambda/sentinel-create-campaign \
  --filter-pattern "📅 Scheduled execution"

# EventBridge Scheduler executions
aws logs filter-log-events --log-group-name /aws/lambda/sentinel-start-campaign \
  --filter-pattern "EventBridge"
```

## 🔮 Future Enhancements

1. **Smart Batching**: Group immediate campaigns into micro-batches
2. **Priority Queues**: Different SQS queues for urgent vs normal campaigns  
3. **Rate Limiting**: Prevent immediate path overload
4. **Retry Logic**: Enhanced error handling for both paths
5. **Analytics**: Track execution path performance metrics

---

This dual-path architecture provides the **best of both worlds**: immediate execution for urgent campaigns and reliable scheduling for planned campaigns, all while maintaining simplicity and cost-effectiveness.