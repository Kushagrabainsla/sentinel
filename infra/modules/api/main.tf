variable "name" { type = string }
variable "tracking_api_arn" { type = string }
variable "segments_api_arn" { type = string }
variable "authorizer_arn" { 
    type = string
    description = "Lambda authorizer invoke ARN for API Gateway v2"
}
variable "auth_api_arn" { type = string }
variable "campaigns_api_arn" { type = string }

# Custom domain configuration
variable "domain_name" { 
    type        = string 
    default     = "api.thesentinel.site"
    description = "Custom domain name for API Gateway"
}

resource "aws_apigatewayv2_api" "http" {
    name          = "${var.name}-http-api"
    protocol_type = "HTTP"
}

# Lambda Authorizer for API Key authentication
resource "aws_apigatewayv2_authorizer" "api_key_auth" {
    api_id                            = aws_apigatewayv2_api.http.id
    authorizer_type                   = "REQUEST"
    authorizer_uri                    = var.authorizer_arn
    name                              = "${var.name}-api-key-authorizer"
    authorizer_payload_format_version = "2.0"
    authorizer_result_ttl_in_seconds  = 30   # Cache authorization results for 30 seconds (balanced for testing + performance)
    identity_sources                  = ["$request.header.X-API-Key"]
}

# Lambda permission for API Gateway to invoke authorizer
resource "aws_lambda_permission" "authorizer_invoke" {
    statement_id  = "AllowAPIGatewayInvokeAuthorizer"
    action        = "lambda:InvokeFunction"
    function_name = "${var.name}-authorizer"
    principal     = "apigateway.amazonaws.com"
    source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}

# ACM Certificate for custom domain (must be in us-east-1 for API Gateway)
resource "aws_acm_certificate" "api_cert" {
    domain_name       = var.domain_name
    validation_method = "DNS"
    
    lifecycle {
        create_before_destroy = true
    }
    
    tags = {
        Name = "${var.name}-api-certificate"
    }
}

# Custom domain for API Gateway
resource "aws_apigatewayv2_domain_name" "api_domain" {
    domain_name = var.domain_name
    
    domain_name_configuration {
        certificate_arn = aws_acm_certificate.api_cert.arn
        endpoint_type   = "REGIONAL"
        security_policy = "TLS_1_2"
    }
    
    depends_on = [aws_acm_certificate_validation.api_cert]
    
    tags = {
        Name = "${var.name}-api-domain"
    }
}

# Certificate validation (requires DNS records)
resource "aws_acm_certificate_validation" "api_cert" {
    certificate_arn = aws_acm_certificate.api_cert.arn
    
    timeouts {
        create = "10m"
    }
}


resource "aws_apigatewayv2_integration" "tracking_api" {
    api_id                 = aws_apigatewayv2_api.http.id
    integration_type       = "AWS_PROXY"
    integration_uri        = var.tracking_api_arn
    payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "segments_api" {
    api_id                 = aws_apigatewayv2_api.http.id
    integration_type       = "AWS_PROXY"
    integration_uri        = var.segments_api_arn
    payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "auth_api" {
    api_id                 = aws_apigatewayv2_api.http.id
    integration_type       = "AWS_PROXY"
    integration_uri        = var.auth_api_arn
    payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "campaigns_api" {
    api_id                 = aws_apigatewayv2_api.http.id
    integration_type       = "AWS_PROXY"
    integration_uri        = var.campaigns_api_arn
    payload_format_version = "2.0"
}

# Campaigns API routes - full CRUD operations
resource "aws_apigatewayv2_route" "campaigns_list" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "GET /v1/campaigns"
    target    = "integrations/${aws_apigatewayv2_integration.campaigns_api.id}"
    authorization_type = "CUSTOM"
    authorizer_id     = aws_apigatewayv2_authorizer.api_key_auth.id
}

resource "aws_apigatewayv2_route" "campaigns_create" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "POST /v1/campaigns"
    target    = "integrations/${aws_apigatewayv2_integration.campaigns_api.id}"
    authorization_type = "CUSTOM"
    authorizer_id     = aws_apigatewayv2_authorizer.api_key_auth.id
}

resource "aws_apigatewayv2_route" "campaigns_get" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "GET /v1/campaigns/{id}"
    target    = "integrations/${aws_apigatewayv2_integration.campaigns_api.id}"
    authorization_type = "CUSTOM"
    authorizer_id     = aws_apigatewayv2_authorizer.api_key_auth.id
}

resource "aws_apigatewayv2_route" "campaigns_update" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "PUT /v1/campaigns/{id}"
    target    = "integrations/${aws_apigatewayv2_integration.campaigns_api.id}"
    authorization_type = "CUSTOM"
    authorizer_id     = aws_apigatewayv2_authorizer.api_key_auth.id
}

resource "aws_apigatewayv2_route" "campaigns_delete" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "DELETE /v1/campaigns/{id}"
    target    = "integrations/${aws_apigatewayv2_integration.campaigns_api.id}"
    authorization_type = "CUSTOM"
    authorizer_id     = aws_apigatewayv2_authorizer.api_key_auth.id
}

resource "aws_apigatewayv2_route" "campaigns_events" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "GET /v1/campaigns/{id}/events"
    target    = "integrations/${aws_apigatewayv2_integration.campaigns_api.id}"
    authorization_type = "CUSTOM"
    authorizer_id     = aws_apigatewayv2_authorizer.api_key_auth.id
}

# Tracking routes  
resource "aws_apigatewayv2_route" "track_open" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "GET /track/open/{proxy+}"
    target    = "integrations/${aws_apigatewayv2_integration.tracking_api.id}"
}

resource "aws_apigatewayv2_route" "track_click" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "GET /track/click/{proxy+}"
    target    = "integrations/${aws_apigatewayv2_integration.tracking_api.id}"
}

resource "aws_apigatewayv2_route" "unsubscribe" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "GET /unsubscribe/{proxy+}"
    target    = "integrations/${aws_apigatewayv2_integration.tracking_api.id}"
}

resource "aws_apigatewayv2_route" "events" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "GET /events/{proxy+}"
    target    = "integrations/${aws_apigatewayv2_integration.tracking_api.id}"
}

# Segments API routes
resource "aws_apigatewayv2_route" "segments_get_list" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "GET /v1/segments"
    target    = "integrations/${aws_apigatewayv2_integration.segments_api.id}"
    authorization_type = "CUSTOM"
    authorizer_id     = aws_apigatewayv2_authorizer.api_key_auth.id
}

resource "aws_apigatewayv2_route" "segments_create" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "POST /v1/segments"
    target    = "integrations/${aws_apigatewayv2_integration.segments_api.id}"
    authorization_type = "CUSTOM"
    authorizer_id     = aws_apigatewayv2_authorizer.api_key_auth.id
}

resource "aws_apigatewayv2_route" "segments_get" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "GET /v1/segments/{id}"
    target    = "integrations/${aws_apigatewayv2_integration.segments_api.id}"
    authorization_type = "CUSTOM"
    authorizer_id     = aws_apigatewayv2_authorizer.api_key_auth.id
}

resource "aws_apigatewayv2_route" "segments_update" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "PUT /v1/segments/{id}"
    target    = "integrations/${aws_apigatewayv2_integration.segments_api.id}"
    authorization_type = "CUSTOM"
    authorizer_id     = aws_apigatewayv2_authorizer.api_key_auth.id
}

resource "aws_apigatewayv2_route" "segments_delete" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "DELETE /v1/segments/{id}"
    target    = "integrations/${aws_apigatewayv2_integration.segments_api.id}"
    authorization_type = "CUSTOM"
    authorizer_id     = aws_apigatewayv2_authorizer.api_key_auth.id
}

resource "aws_apigatewayv2_route" "segments_get_emails" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "GET /v1/segments/{id}/emails"
    target    = "integrations/${aws_apigatewayv2_integration.segments_api.id}"
    authorization_type = "CUSTOM"
    authorizer_id     = aws_apigatewayv2_authorizer.api_key_auth.id
}

# Support legacy /contacts endpoint for backward compatibility
resource "aws_apigatewayv2_route" "segments_get_contacts" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "GET /v1/segments/{id}/contacts"
    target    = "integrations/${aws_apigatewayv2_integration.segments_api.id}"
    authorization_type = "CUSTOM"
    authorizer_id     = aws_apigatewayv2_authorizer.api_key_auth.id
}

resource "aws_apigatewayv2_route" "segments_add_emails" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "POST /v1/segments/{id}/emails"
    target    = "integrations/${aws_apigatewayv2_integration.segments_api.id}"
    authorization_type = "CUSTOM"
    authorizer_id     = aws_apigatewayv2_authorizer.api_key_auth.id
}

resource "aws_apigatewayv2_route" "segments_remove_emails" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "DELETE /v1/segments/{id}/emails"
    target    = "integrations/${aws_apigatewayv2_integration.segments_api.id}"
    authorization_type = "CUSTOM"
    authorizer_id     = aws_apigatewayv2_authorizer.api_key_auth.id
}

resource "aws_apigatewayv2_route" "segments_refresh_counts" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "POST /v1/segments/refresh-counts"
    target    = "integrations/${aws_apigatewayv2_integration.segments_api.id}"
    authorization_type = "CUSTOM"
    authorizer_id     = aws_apigatewayv2_authorizer.api_key_auth.id
}

# Auth API routes (no authorization required for registration/login)
resource "aws_apigatewayv2_route" "auth_register" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "POST /v1/auth/register"
    target    = "integrations/${aws_apigatewayv2_integration.auth_api.id}"
}

resource "aws_apigatewayv2_route" "auth_login" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "POST /v1/auth/login"
    target    = "integrations/${aws_apigatewayv2_integration.auth_api.id}"
}

resource "aws_apigatewayv2_route" "auth_me" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "GET /v1/auth/me"
    target    = "integrations/${aws_apigatewayv2_integration.auth_api.id}"
    authorization_type = "CUSTOM"
    authorizer_id     = aws_apigatewayv2_authorizer.api_key_auth.id
}

resource "aws_apigatewayv2_route" "auth_regenerate_key" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "POST /v1/auth/regenerate-key"
    target    = "integrations/${aws_apigatewayv2_integration.auth_api.id}"
    authorization_type = "CUSTOM"
    authorizer_id     = aws_apigatewayv2_authorizer.api_key_auth.id
}


resource "aws_lambda_permission" "api_invoke_tracking" {
    statement_id  = "AllowAPIGatewayInvokeTracking"
    action        = "lambda:InvokeFunction"
    function_name = var.tracking_api_arn
    principal     = "apigateway.amazonaws.com"
    source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_invoke_segments" {
    statement_id  = "AllowAPIGatewayInvokeSegments"
    action        = "lambda:InvokeFunction"
    function_name = var.segments_api_arn
    principal     = "apigateway.amazonaws.com"
    source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_invoke_auth" {
    statement_id  = "AllowAPIGatewayInvokeAuth"
    action        = "lambda:InvokeFunction"
    function_name = var.auth_api_arn
    principal     = "apigateway.amazonaws.com"
    source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_invoke_campaigns" {
    statement_id  = "AllowAPIGatewayInvokeCampaigns"
    action        = "lambda:InvokeFunction"
    function_name = var.campaigns_api_arn
    principal     = "apigateway.amazonaws.com"
    source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}

resource "aws_apigatewayv2_stage" "default" {
    api_id      = aws_apigatewayv2_api.http.id
    name        = "$default"
    auto_deploy = true
}

# Map custom domain to API Gateway stage
resource "aws_apigatewayv2_api_mapping" "api_mapping" {
    api_id      = aws_apigatewayv2_api.http.id
    domain_name = aws_apigatewayv2_domain_name.api_domain.id
    stage       = aws_apigatewayv2_stage.default.id
}

output "invoke_url" {
    value = aws_apigatewayv2_api.http.api_endpoint
}

output "custom_domain_url" {
    value = "https://${var.domain_name}"
}

output "domain_validation_records" {
    description = "DNS records needed for domain validation"
    value = {
        for dvo in aws_acm_certificate.api_cert.domain_validation_options : dvo.domain_name => {
            name   = dvo.resource_record_name
            record = dvo.resource_record_value
            type   = dvo.resource_record_type
        }
    }
}

output "api_domain_target" {
    description = "DNS target for CNAME record"
    value       = aws_apigatewayv2_domain_name.api_domain.domain_name_configuration[0].target_domain_name
}
