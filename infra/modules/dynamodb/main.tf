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

resource "aws_dynamodb_table" "users" {
  name         = "${var.name}-users"
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
  attribute {
    name = "api_key"
    type = "S"
  }
  global_secondary_index {
    name               = "email_index"
    hash_key           = "email"
    projection_type    = "ALL"
  }
  global_secondary_index {
    name               = "api_key_index"
    hash_key           = "api_key"
    projection_type    = "ALL"
  }
}

resource "aws_dynamodb_table" "campaigns" {
  name         = "${var.name}-campaigns"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "owner_id"
    type = "S"
  }
  global_secondary_index {
    name               = "owner_index"
    hash_key           = "owner_id"
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

resource "aws_dynamodb_table" "segments" {
  name         = "${var.name}-segments"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "owner_id"
    type = "S"
  }
  global_secondary_index {
    name               = "owner_index"
    hash_key           = "owner_id"
    projection_type    = "ALL"
  }
}

resource "aws_dynamodb_table" "link_mappings" {
  name         = "${var.name}-link-mappings"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "tracking_id"
  attribute {
    name = "tracking_id"
    type = "S"
  }
  attribute {
    name = "campaign_id"
    type = "S"
  }
  attribute {
    name = "recipient_id"
    type = "S"
  }
  global_secondary_index {
    name               = "campaign_recipient_index"
    hash_key           = "campaign_id"
    range_key          = "recipient_id"
    projection_type    = "ALL"
  }
  
  # TTL for automatic cleanup of old tracking links (90 days)
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }
}

output "users_table" {
  value = aws_dynamodb_table.users.name
}

output "campaigns_table" {
  value = aws_dynamodb_table.campaigns.name
}



output "segments_table" {
  value = aws_dynamodb_table.segments.name
}

output "events_table" {
  value = aws_dynamodb_table.events.name
}

output "link_mappings_table" {
  value = aws_dynamodb_table.link_mappings.name
}
