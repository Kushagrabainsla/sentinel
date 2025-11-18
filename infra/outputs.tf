output "api_url" {
    value = module.api.invoke_url
}

output "api_gateway_url" {
    description = "API Gateway URL"
    value       = module.api.invoke_url
}

output "send_queue_url" {
    value = module.queues.send_queue_url
}

# DynamoDB outputs
output "dynamodb_campaigns_table" {
    description = "DynamoDB campaigns table name"
    value       = module.dynamodb.campaigns_table
}

output "dynamodb_contacts_table" {
    description = "DynamoDB contacts table name"  
    value       = module.dynamodb.contacts_table
}

output "dynamodb_recipients_table" {
    description = "DynamoDB recipients table name"
    value       = module.dynamodb.recipients_table
}

output "dynamodb_events_table" {
    description = "DynamoDB events table name"
    value       = module.dynamodb.events_table
}

# SES DKIM Configuration
output "ses_dkim_tokens" {
    description = "DKIM tokens for DNS CNAME records"
    value       = module.ses.dkim_tokens
}

output "ses_domain_verification_token" {
    description = "Domain verification token for DNS TXT record"
    value       = module.ses.domain_verification_token
}
