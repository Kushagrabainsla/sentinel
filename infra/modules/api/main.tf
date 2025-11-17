variable "name" { type = string }
variable "create_campaign_arn" { type = string }

resource "aws_apigatewayv2_api" "http" {
    name          = "${var.name}-http-api"
    protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "create_campaign" {
    api_id                 = aws_apigatewayv2_api.http.id
    integration_type       = "AWS_PROXY"
    integration_uri        = var.create_campaign_arn
    payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "post_campaigns" {
    api_id    = aws_apigatewayv2_api.http.id
    route_key = "POST /v1/campaigns"
    target    = "integrations/${aws_apigatewayv2_integration.create_campaign.id}"
}

resource "aws_lambda_permission" "api_invoke" {
    statement_id  = "AllowAPIGatewayInvokeCreate"
    action        = "lambda:InvokeFunction"
    function_name = var.create_campaign_arn
    principal     = "apigateway.amazonaws.com"
    source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}

resource "aws_apigatewayv2_stage" "default" {
    api_id      = aws_apigatewayv2_api.http.id
    name        = "$default"
    auto_deploy = true
}

output "invoke_url" {
    value = aws_apigatewayv2_api.http.api_endpoint
}
