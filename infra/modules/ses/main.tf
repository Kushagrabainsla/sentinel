variable "domain" { type = string }

# Domain identity for SES
resource "aws_ses_domain_identity" "main" {
  domain = var.domain
}

# Enable DKIM signing
resource "aws_ses_domain_dkim" "main" {
  domain = aws_ses_domain_identity.main.domain
}

# Email identity for the specific sender address
resource "aws_ses_email_identity" "sender" {
  email = "no-reply@${var.domain}"
}

# Output DKIM tokens for DNS configuration
output "dkim_tokens" {
  description = "DKIM tokens that need to be added to DNS as CNAME records"
  value       = aws_ses_domain_dkim.main.dkim_tokens
}

output "domain_verification_token" {
  description = "Domain verification token for DNS TXT record"
  value       = aws_ses_domain_identity.main.verification_token
}

output "domain_identity_arn" {
  description = "ARN of the SES domain identity"
  value       = aws_ses_domain_identity.main.arn
}