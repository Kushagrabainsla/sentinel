# Campaign Schema Documentation

## Optimized Campaign Data Structure

The campaign schema has been optimized for storage efficiency using epoch timestamps, character-based enums, and HTML-only email content.

### Core Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `id` | string (UUID) | Unique campaign identifier | Yes |
| `name` | string | Campaign display name | Yes |
| `created_at` | integer (epoch) | Campaign creation timestamp | Yes |
| `updated_at` | integer (epoch) | Last update timestamp | Yes |
| `type` | string (1 char) | Campaign type enum | Yes |

### Email Content Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `email_subject` | string | Email subject line | Yes |
| `email_body` | string | HTML email body content | Yes |
| `from_email` | string | Sender email address | No (defaults to "noreply@thesentinel.site") |
| `from_name` | string | Sender display name | No (defaults to "Sentinel") |

### Campaign Configuration

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `segment_id` | string | Target audience segment identifier | Yes |
| `schedule_at` | integer (epoch) | Scheduled send timestamp for scheduled campaigns | Conditional |
| `state` | string (1-2 chars) | Current execution state enum | Yes |
| `status` | string (1 char) | Campaign status enum | Yes |

### Additional Metadata

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `tags` | array | Campaign tags for categorization | [] |
| `metadata` | object | Additional custom fields and data | {} |

## Enum Values

### Campaign Type (`type`)
- `"I"`: Immediate execution
- `"S"`: Scheduled execution

### Campaign State (`state`)
- `"SC"`: Scheduled for future execution
- `"P"`: Pending immediate execution  
- `"SE"`: Currently sending
- `"D"`: Done/Completed
- `"F"`: Failed

### Campaign Status (`status`)
- `"A"`: Active campaign
- `"I"`: Inactive campaign

## Campaign Types

### Immediate Campaigns
- `type`: `"I"` (user-specified)
- Executed immediately upon creation
- `schedule_at` must be null/not provided
- Initial `state`: `"P"` (Pending)

### Scheduled Campaigns
- `type`: `"S"` (user-specified)
- Executed at a future time via EventBridge Scheduler
- `schedule_at` is required (provided as epoch timestamp)
- Initial `state`: `"SC"` (Scheduled)

## State Transitions

```
SC → SE → D  (Scheduled campaigns)
P → SE → D   (Immediate campaigns)
Any → F      (Failed state)
```

## API Validation Rules

### Campaign Type Requirements
- **`type`** field is required in API requests
- **Immediate Campaigns** (`type="I"`):
  - `schedule_at` must NOT be provided
  - Campaign executes immediately upon creation
- **Scheduled Campaigns** (`type="S"`):
  - `schedule_at` is REQUIRED
  - Must be provided as epoch timestamp (integer)

### Required Fields
- `name`: Campaign display name
- `type`: Campaign type ("I" or "S") 
- `subject`: Email subject line
- `html_body`: HTML email content
- `schedule_at`: Required only for scheduled campaigns (as epoch timestamp)

## Email Content Handling

- **HTML Content**: Primary email format stored in `email_body`
- **Text Content**: Automatically generated from HTML during sending
- **Fallback**: If HTML-to-text conversion fails, uses "Please view this email in HTML format."

## Simplified Status Management

| Aspect | CampaignState | CampaignStatus |
|--------|---------------|----------------|
| **Control** | System-managed | User-managed |
| **Purpose** | Technical execution | Business management |
| **Changes** | Automatic during sending | Manual user actions |
| **Values** | SC, P, SE, D, F | A, I |

## Example Scenarios

1. **Active Scheduled Campaign**: `status="A"`, `state="SC"`
2. **Inactive Campaign**: `status="I"`, `state="SC"` (won't execute even if scheduled)
3. **Currently Sending**: `status="A"`, `state="SE"`
4. **Inactive During Execution**: `status="I"`, `state="SE"` (will complete but marked inactive)
5. **Successfully Completed**: `status="A"` or `"I"`, `state="D"`

## Analytics Separation

Analytics data (recipient counts, opens, clicks, etc.) are tracked separately in dedicated tables/services to keep the campaign table lean and optimized.

## Example Campaign Record

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Welcome Series - Part 1",
  "created_at": 1700000000,
  "updated_at": 1700000000,
  "type": "S",
  "email_subject": "Welcome to Sentinel!",
  "email_body": "<html><body><h1>Welcome!</h1><p>Thanks for joining us.</p></body></html>",
  "from_email": "hello@thesentinel.site", 
  "from_name": "Sentinel Team",
  "segment_id": "new_users",
  "schedule_at": 1700086400,
  "state": "SC",
  "status": "A",
  "tags": ["welcome", "onboarding"],
  "metadata": {
    "created_by": "user123",
    "campaign_series": "welcome_flow"
  }
}
```

## API Examples

### Immediate Campaign
```json
{
  "name": "Flash Sale",
  "type": "I",
  "subject": "24-Hour Flash Sale!",
  "html_body": "<html><body><h1>Flash Sale!</h1></body></html>"
  // schedule_at NOT allowed
}
```

### Scheduled Campaign
```json
{
  "name": "Weekly Newsletter", 
  "type": "S",
  "subject": "This Week's Updates",
  "html_body": "<html><body><h1>Newsletter</h1></body></html>",
  "schedule_at": 1700086400  // Required (epoch timestamp)
}
```

## Helper Functions

### `update_campaign_metadata(campaign_id, **metadata_updates)`
Updates campaign metadata fields like tags and custom metadata.

```python
update_campaign_metadata(campaign_id, tags=["new-tag"], metadata={"key": "value"})
```

### `update_campaign_status(campaign_id, status)`
Updates campaign status using enum values.

```python
from common_db import CampaignStatus
update_campaign_status(campaign_id, CampaignStatus.INACTIVE)
```

### `update_campaign_state(campaign_id, state)`
Updates campaign execution state using enum values.

```python
from common_db import CampaignState
update_campaign_state(campaign_id, CampaignState.SENDING)
```