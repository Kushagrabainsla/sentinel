output "api_url" {
    value = module.api.invoke_url
}

output "api_gateway_url" {
    description = "API Gateway URL"
    value       = module.api.invoke_url
}

output "custom_domain_url" {
    description = "Custom domain URL for API"
    value       = module.api.custom_domain_url
}

output "domain_validation_records" {
    description = "DNS records needed for SSL certificate validation"
    value       = module.api.domain_validation_records
}

output "api_domain_target" {
    description = "Target domain for CNAME record (api.thesentinel.site -> this value)"
    value       = module.api.api_domain_target
}

output "send_queue_url" {
    value = module.queues.send_queue_url
}

# DynamoDB outputs
output "dynamodb_campaigns_table" {
    description = "DynamoDB campaigns table name"
    value       = module.dynamodb.campaigns_table
}



output "dynamodb_segments_table" {
    description = "DynamoDB segments table name"
    value       = module.dynamodb.segments_table
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

output "assets_bucket_name" {
    description = "S3 assets bucket name"
    value       = module.s3_assets.bucket_name
}

output "sentinel_logo_url" {
    description = "URL for Sentinel logo (used for tracking)"
    value       = module.s3_assets.sentinel_logo_url
}
