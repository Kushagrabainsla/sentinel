# AI Features Infrastructure

# 1. DynamoDB Table for Optimization Insights
resource "aws_dynamodb_table" "optimization_insights" {
    name         = "${local.name}-optimization-insights"
    billing_mode = "PAY_PER_REQUEST"
    hash_key     = "insight_id"
    range_key    = "timestamp"
    
    attribute {
        name = "insight_id"
        type = "S"
    }
    
    attribute {
        name = "timestamp"
        type = "S"
    }
}

# 2. Lambda Layer for AI Dependencies
data "archive_file" "ai_dependencies_layer" {
    type        = "zip"
    source_dir  = "${path.module}/layers/ai_dependencies"
    output_path = "${path.module}/.artifacts/ai_dependencies.zip"
}

resource "aws_lambda_layer_version" "ai_dependencies" {
    filename            = data.archive_file.ai_dependencies_layer.output_path
    layer_name          = "${local.name}-ai-dependencies"
    compatible_runtimes = ["python3.11"]
    source_code_hash    = data.archive_file.ai_dependencies_layer.output_base64sha256
}

# 3. Lambda Functions

# Archive for Analyze Optimization
data "archive_file" "analyze_optimization" {
    type        = "zip"
    source_dir  = "${path.module}/../services/ai_features"
    output_path = "${path.module}/.artifacts/analyze_optimization.zip"
    excludes    = ["__pycache__", "*.pyc"]
}

# Note: We are zipping the entire ai_features directory to include shared code.
# The handler will be services.ai_features.analyze_optimization.handler.analyze_optimization_agent
# But wait, if we zip `services/ai_features`, the root of the zip is `ai_features`?
# No, source_dir content is at root.
# So `analyze_optimization/handler.py` is at `analyze_optimization/handler.py`.
# And `shared/gemini_client.py` is at `shared/gemini_client.py`.
# So imports should be `from shared.gemini_client import ...`
# But my code uses `from services.ai_features.shared.gemini_client import ...`
# This assumes `services` is in the path.
# I should adjust the source_dir or the imports.
# If I zip `services`, then `ai_features` is a folder.
# Let's zip `services` but only include `ai_features`? No, `archive_file` doesn't support include patterns easily.
# I will zip `${path.module}/../services/ai_features` and change imports in python code to relative or `ai_features...`?
# If I zip `ai_features` folder content:
# root/
#   analyze_optimization/
#   generate_subject_lines/
#   shared/
# Then `import shared.gemini_client` works.
# But my code has `from services.ai_features.shared.gemini_client`.
# I should change the python code to `from shared.gemini_client import ...` OR `from .shared.gemini_client import ...`
# OR I zip the parent `services` directory? That might be too big.
# I will fix the python imports to be `shared.gemini_client` and zip `ai_features` content.

resource "aws_lambda_function" "analyze_optimization" {
    function_name    = "${local.name}-analyze-optimization"
    role             = module.iam.roles.lambda_exec
    handler          = "analyze_optimization.handler.analyze_optimization_agent"
    runtime          = "python3.11"
    filename         = data.archive_file.analyze_optimization.output_path
    source_code_hash = data.archive_file.analyze_optimization.output_base64sha256
    timeout          = 60
    layers           = [aws_lambda_layer_version.ai_dependencies.arn]
    
    environment {
        variables = {
            CAMPAIGNS_TABLE = module.dynamodb.campaigns_table
            EVENTS_TABLE    = module.dynamodb.events_table
            INSIGHTS_TABLE  = aws_dynamodb_table.optimization_insights.name
            GEMINI_API_KEY  = var.GEMINI_API_KEY
        }
    }
}

resource "aws_lambda_function" "generate_subject_lines" {
    function_name    = "${local.name}-generate-subject-lines"
    role             = module.iam.roles.lambda_exec
    handler          = "generate_subject_lines.handler.generate_subject_lines"
    runtime          = "python3.11"
    filename         = data.archive_file.analyze_optimization.output_path # Reusing the same zip
    source_code_hash = data.archive_file.analyze_optimization.output_base64sha256
    timeout          = 30
    layers           = [aws_lambda_layer_version.ai_dependencies.arn]
    
    environment {
        variables = {
            GEMINI_API_KEY = var.GEMINI_API_KEY
        }
    }
}

# 4. API Gateway Integrations

resource "aws_apigatewayv2_integration" "analyze_optimization" {
    api_id                 = module.api.http_api_id
    integration_type       = "AWS_PROXY"
    integration_uri        = aws_lambda_function.analyze_optimization.arn
    payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "generate_subject_lines" {
    api_id                 = module.api.http_api_id
    integration_type       = "AWS_PROXY"
    integration_uri        = aws_lambda_function.generate_subject_lines.arn
    payload_format_version = "2.0"
}

# 5. API Routes

resource "aws_apigatewayv2_route" "analyze_optimization" {
    api_id    = module.api.http_api_id
    route_key = "GET /api/analyze-optimization"
    target    = "integrations/${aws_apigatewayv2_integration.analyze_optimization.id}"
}

resource "aws_apigatewayv2_route" "generate_subject_lines" {
    api_id    = module.api.http_api_id
    route_key = "POST /api/generate-subject-lines"
    target    = "integrations/${aws_apigatewayv2_integration.generate_subject_lines.id}"
}

# 6. Permissions

resource "aws_lambda_permission" "api_invoke_analyze" {
    statement_id  = "AllowAPIGatewayInvokeAnalyze"
    action        = "lambda:InvokeFunction"
    function_name = aws_lambda_function.analyze_optimization.arn
    principal     = "apigateway.amazonaws.com"
    source_arn    = "${module.api.http_api_execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_invoke_generate" {
    statement_id  = "AllowAPIGatewayInvokeGenerate"
    action        = "lambda:InvokeFunction"
    function_name = aws_lambda_function.generate_subject_lines.arn
    principal     = "apigateway.amazonaws.com"
    source_arn    = "${module.api.http_api_execution_arn}/*/*"
}

# 7. Single Campaign Analyzer

resource "aws_lambda_function" "analyze_campaign" {
    function_name    = "${local.name}-analyze-campaign"
    role             = module.iam.roles.lambda_exec
    handler          = "analyze_campaign.handler.analyze_campaign"
    runtime          = "python3.11"
    filename         = data.archive_file.analyze_optimization.output_path # Reusing the same zip
    source_code_hash = data.archive_file.analyze_optimization.output_base64sha256
    timeout          = 60
    layers           = [aws_lambda_layer_version.ai_dependencies.arn]
    
    environment {
        variables = {
            CAMPAIGNS_TABLE = module.dynamodb.campaigns_table
            EVENTS_TABLE    = module.dynamodb.events_table
            GEMINI_API_KEY  = var.GEMINI_API_KEY
        }
    }
}

resource "aws_apigatewayv2_integration" "analyze_campaign" {
    api_id                 = module.api.http_api_id
    integration_type       = "AWS_PROXY"
    integration_uri        = aws_lambda_function.analyze_campaign.arn
    payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "analyze_campaign" {
    api_id    = module.api.http_api_id
    route_key = "GET /api/analyze-campaign"
    target    = "integrations/${aws_apigatewayv2_integration.analyze_campaign.id}"
}

resource "aws_lambda_permission" "api_invoke_analyze_campaign" {
    statement_id  = "AllowAPIGatewayInvokeAnalyzeCampaign"
    action        = "lambda:InvokeFunction"
    function_name = aws_lambda_function.analyze_campaign.arn
    principal     = "apigateway.amazonaws.com"
    source_arn    = "${module.api.http_api_execution_arn}/*/*"
}
