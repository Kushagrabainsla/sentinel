variable "name" { type = string }
variable "create_campaign_arn" { type = string }
variable "tracking_api_arn" { type = string }

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

resource "aws_apigatewayv2_integration" "create_campaign" {
    api_id                 = aws_apigatewayv2_api.http.id
    integration_type       = "AWS_PROXY"
    integration_uri        = var.create_campaign_arn
    payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "tracking_api" {
    api_id                 = aws_apigatewayv2_api.http.id
    integration_type       = "AWS_PROXY"
    integration_uri        = var.tracking_api_arn
    payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "post_campaigns" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "POST /v1/campaigns"
    target    = "integrations/${aws_apigatewayv2_integration.create_campaign.id}"
}

# Tracking routes
resource "aws_apigatewayv2_route" "track_open" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "GET /track/open/{campaign_id}/{recipient_id}"
    target    = "integrations/${aws_apigatewayv2_integration.tracking_api.id}"
}

resource "aws_apigatewayv2_route" "track_click" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "GET /track/click/{tracking_id}"
    target    = "integrations/${aws_apigatewayv2_integration.tracking_api.id}"
}

resource "aws_apigatewayv2_route" "unsubscribe" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "GET /unsubscribe/{token}"
    target    = "integrations/${aws_apigatewayv2_integration.tracking_api.id}"
}

resource "aws_lambda_permission" "api_invoke" {
    statement_id  = "AllowAPIGatewayInvokeCreate"
    action        = "lambda:InvokeFunction"
    function_name = var.create_campaign_arn
    principal     = "apigateway.amazonaws.com"
    source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_invoke_tracking" {
    statement_id  = "AllowAPIGatewayInvokeTracking"
    action        = "lambda:InvokeFunction"
    function_name = var.tracking_api_arn
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
