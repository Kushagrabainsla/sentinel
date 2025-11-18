variable "name" { type = string }
variable "read_capacity" {
  type    = number
  default = 5
}

variable "write_capacity" {
  type    = number
  default = 5
}

variable "enable_global_tables" {
  type    = bool
  default = false
}

variable "global_table_regions" {
  type        = list(string)
  default     = []
  description = "List of regions for global tables"
}

resource "aws_dynamodb_table" "campaigns" {
  name         = "${var.name}-campaigns"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  attribute {
    name = "id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "contacts" {
  name         = "${var.name}-contacts"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "email"
    type = "S"
  }
  global_secondary_index {
    name               = "email_index"
    hash_key           = "email"
    projection_type    = "ALL"
  }
}

resource "aws_dynamodb_table" "recipients" {
  name         = "${var.name}-recipients"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "campaign_id"
  range_key    = "recipient_id"
  attribute {
    name = "campaign_id"
    type = "S"
  }
  attribute {
    name = "recipient_id"
    type = "S"
  }
  attribute {
    name = "email"
    type = "S"
  }
  global_secondary_index {
    name               = "campaign_email_index"
    hash_key           = "campaign_id"
    range_key          = "email"
    projection_type    = "ALL"
  }
}

resource "aws_dynamodb_table" "events" {
  name         = "${var.name}-events"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "campaign_id"
    type = "S"
  }
  global_secondary_index {
    name            = "campaign_index"
    hash_key        = "campaign_id"
    projection_type = "ALL"
  }
}

output "campaigns_table" {
  value = aws_dynamodb_table.campaigns.name
}

output "contacts_table" {
  value = aws_dynamodb_table.contacts.name
}

output "recipients_table" {
  value = aws_dynamodb_table.recipients.name
}

output "events_table" {
  value = aws_dynamodb_table.events.name
}
