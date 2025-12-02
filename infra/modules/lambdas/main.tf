variable "name"              { type = string }
variable "region"            { type = string }
variable "roles"             { type = any }
variable "queues"            { type = any }

variable "dynamodb_users_table"         { type = string }
variable "dynamodb_campaigns_table"     { type = string }
variable "dynamodb_segments_table"      { type = string }
variable "dynamodb_events_table"        { type = string }
variable "dynamodb_link_mappings_table" { type = string }

variable "ses_from_address"  { type = string }

variable "scheduler_invoke_role_arn" { type = string }
variable "tracking_base_url" { type = string }
variable "assets_bucket_name" { type = string }
variable "sentinel_logo_url" { type = string }

# Configuration constants
locals {
    # Lambda runtime and handler
    lambda_runtime = "python3.11"
    lambda_handler = "handler.lambda_handler"
    
    # Timeout configurations (in seconds)
    timeout_short  = 10   # For authorizer
    timeout_medium = 30   # For most APIs
    timeout_long   = 60   # For heavy operations (AI, campaigns, send_worker)
    
    # Memory configurations (in MB)
    memory_default = 128
    memory_medium  = 256  # For send_worker
    memory_high    = 512  # For AI workloads
    
    # Reserved concurrency settings
    concurrency_ai        = 20   # AI workloads (generate_email, generate_insights)
    concurrency_api       = 20   # Standard APIs
    concurrency_auth      = 50   # Authorizer (high traffic)
    concurrency_worker    = 20   # send_worker safety net
    concurrency_analyzer  = 10   # ab_test_analyzer (background job)
    
    # SES rate limiting via SQS scaling
    ses_batch_size              = 7    # Emails per Lambda invocation
    ses_max_concurrency         = 2    # Max concurrent Lambda executions
    ses_batching_window_seconds = 1    # Wait time to collect full batch
    # Throughput: ses_max_concurrency × ses_batch_size = 2 × 7 = 14 emails/sec
    
    # CloudWatch log retention
    log_retention_days = 30
}

resource "aws_lambda_function" "generate_email" {
    function_name    = "${var.name}-generate-email"
    role             = var.roles.lambda_exec
    handler          = local.lambda_handler
    runtime          = local.lambda_runtime
    filename         = "${path.module}/.artifacts/generate_email.zip"
    source_code_hash = filebase64sha256("${path.module}/.artifacts/generate_email.zip")
    timeout          = local.timeout_medium
    memory_size      = local.memory_high
    
    environment {
        variables = {}
    }
    
    depends_on = [aws_cloudwatch_log_group.generate_email]
}

resource "aws_lambda_function" "generate_insights" {
    function_name    = "${var.name}-generate-insights"
    role             = var.roles.lambda_exec
    handler          = local.lambda_handler
    runtime          = local.lambda_runtime
    filename         = "${path.module}/.artifacts/generate_insights.zip"
    source_code_hash = filebase64sha256("${path.module}/.artifacts/generate_insights.zip")
    timeout          = local.timeout_long
    memory_size      = local.memory_high
    
    environment {
        variables = {}
    }
    
    depends_on = [aws_cloudwatch_log_group.generate_insights]
}


resource "aws_lambda_function" "start_campaign" {
    function_name    = "${var.name}-start-campaign"
    role             = var.roles.lambda_exec
    handler          = local.lambda_handler
    runtime          = local.lambda_runtime
    filename         = "${path.module}/.artifacts/start_campaign.zip"
    source_code_hash = filebase64sha256("${path.module}/.artifacts/start_campaign.zip")
    timeout          = local.timeout_long
    
    environment {
        variables = {
            DYNAMODB_CAMPAIGNS_TABLE  = var.dynamodb_campaigns_table
            DYNAMODB_SEGMENTS_TABLE   = var.dynamodb_segments_table
            DYNAMODB_EVENTS_TABLE     = var.dynamodb_events_table
            SEND_QUEUE_URL = var.queues.send_queue_url
            AB_TEST_ANALYZER_LAMBDA_ARN = aws_lambda_function.ab_test_analyzer.arn
            EVENTBRIDGE_ROLE_ARN        = var.scheduler_invoke_role_arn
        }
    }
    
    depends_on = [aws_cloudwatch_log_group.start_campaign]
}

resource "aws_lambda_function" "send_worker" {
    function_name    = "${var.name}-send-worker"
    role             = var.roles.lambda_exec
    handler          = local.lambda_handler
    runtime          = local.lambda_runtime
    filename         = "${path.module}/.artifacts/send_worker.zip"
    source_code_hash = filebase64sha256("${path.module}/.artifacts/send_worker.zip")
    timeout          = local.timeout_long
    memory_size      = local.memory_medium
    reserved_concurrent_executions = local.concurrency_worker

    environment {
        variables = {
            DYNAMODB_CAMPAIGNS_TABLE     = var.dynamodb_campaigns_table
            DYNAMODB_SEGMENTS_TABLE      = var.dynamodb_segments_table
            DYNAMODB_EVENTS_TABLE        = var.dynamodb_events_table
            DYNAMODB_LINK_MAPPINGS_TABLE = var.dynamodb_link_mappings_table
            SES_FROM_ADDRESS             = var.ses_from_address
            TRACKING_BASE_URL            = var.tracking_base_url
            S3_ASSETS_BUCKET             = var.assets_bucket_name
            SENTINEL_LOGO_URL            = var.sentinel_logo_url
        }
    }
    
    depends_on = [aws_cloudwatch_log_group.send_worker]
}

resource "aws_lambda_event_source_mapping" "send_worker_sqs" {
    event_source_arn = var.queues.send_queue_arn
    function_name    = aws_lambda_function.send_worker.arn
    
    batch_size       = local.ses_batch_size
    maximum_batching_window_in_seconds = local.ses_batching_window_seconds
    
    # CRITICAL: SES rate limiting via concurrency control
    # Throughput = ses_max_concurrency × ses_batch_size = 2 × 7 = 14 emails/sec
    scaling_config {
        maximum_concurrency = local.ses_max_concurrency
    }
}



resource "aws_lambda_function" "tracking_api" {
    function_name    = "${var.name}-tracking-api"
    role             = var.roles.lambda_exec
    handler          = local.lambda_handler
    runtime          = local.lambda_runtime
    filename         = "${path.module}/.artifacts/tracking_api.zip"
    source_code_hash = filebase64sha256("${path.module}/.artifacts/tracking_api.zip")
    timeout          = local.timeout_medium
    
    environment {
        variables = {
            DYNAMODB_CAMPAIGNS_TABLE     = var.dynamodb_campaigns_table
            DYNAMODB_SEGMENTS_TABLE      = var.dynamodb_segments_table
            DYNAMODB_EVENTS_TABLE        = var.dynamodb_events_table
            DYNAMODB_LINK_MAPPINGS_TABLE = var.dynamodb_link_mappings_table
            S3_ASSETS_BUCKET             = var.assets_bucket_name
            SENTINEL_LOGO_URL            = var.sentinel_logo_url
        }
    }
    
    depends_on = [aws_cloudwatch_log_group.tracking_api]
}

resource "aws_lambda_function" "segments_api" {
    function_name    = "${var.name}-segments-api"
    role             = var.roles.lambda_exec
    handler          = local.lambda_handler
    runtime          = local.lambda_runtime
    filename         = "${path.module}/.artifacts/segments_api.zip"
    source_code_hash = filebase64sha256("${path.module}/.artifacts/segments_api.zip")
    timeout          = local.timeout_medium
    
    environment {
        variables = {
            DYNAMODB_CAMPAIGNS_TABLE = var.dynamodb_campaigns_table
            DYNAMODB_SEGMENTS_TABLE  = var.dynamodb_segments_table
            DYNAMODB_EVENTS_TABLE    = var.dynamodb_events_table
        }
    }
    
    depends_on = [aws_cloudwatch_log_group.segments_api]
}

resource "aws_lambda_function" "authorizer" {
    function_name    = "${var.name}-authorizer"
    role             = var.roles.lambda_exec
    handler          = local.lambda_handler
    runtime          = local.lambda_runtime
    filename         = "${path.module}/.artifacts/authorizer.zip"
    source_code_hash = filebase64sha256("${path.module}/.artifacts/authorizer.zip")
    timeout          = local.timeout_short
    
    environment {
        variables = {
            DYNAMODB_USERS_TABLE = var.dynamodb_users_table
        }
    }
    
    depends_on = [aws_cloudwatch_log_group.authorizer]
}

resource "aws_lambda_function" "auth_api" {
    function_name    = "${var.name}-auth-api"
    role             = var.roles.lambda_exec
    handler          = local.lambda_handler
    runtime          = local.lambda_runtime
    filename         = "${path.module}/.artifacts/auth_api.zip"
    source_code_hash = filebase64sha256("${path.module}/.artifacts/auth_api.zip")
    timeout          = local.timeout_medium
    
    environment {
        variables = {
            DYNAMODB_USERS_TABLE = var.dynamodb_users_table
        }
    }
    
    depends_on = [aws_cloudwatch_log_group.auth_api]
}

resource "aws_lambda_function" "campaigns_api" {
    function_name    = "${var.name}-campaigns-api"
    role             = var.roles.lambda_exec
    handler          = local.lambda_handler
    runtime          = local.lambda_runtime
    filename         = "${path.module}/.artifacts/campaigns_api.zip"
    source_code_hash = filebase64sha256("${path.module}/.artifacts/campaigns_api.zip")
    timeout          = local.timeout_medium
    
    environment {
        variables = {
            DYNAMODB_CAMPAIGNS_TABLE     = var.dynamodb_campaigns_table
            DYNAMODB_SEGMENTS_TABLE      = var.dynamodb_segments_table
            DYNAMODB_EVENTS_TABLE        = var.dynamodb_events_table
            START_CAMPAIGN_LAMBDA_ARN    = aws_lambda_function.start_campaign.arn
            EVENTBRIDGE_ROLE_ARN         = var.scheduler_invoke_role_arn
        }
    }
    
    depends_on = [aws_cloudwatch_log_group.campaigns_api]
}

resource "aws_lambda_function" "ab_test_analyzer" {
    function_name    = "${var.name}-ab-test-analyzer"
    role             = var.roles.lambda_exec
    handler          = local.lambda_handler
    runtime          = local.lambda_runtime
    filename         = "${path.module}/.artifacts/ab_test_analyzer.zip"
    source_code_hash = filebase64sha256("${path.module}/.artifacts/ab_test_analyzer.zip")
    timeout          = local.timeout_long
    
    environment {
        variables = {
            DYNAMODB_CAMPAIGNS_TABLE = var.dynamodb_campaigns_table
            DYNAMODB_SEGMENTS_TABLE  = var.dynamodb_segments_table
            DYNAMODB_EVENTS_TABLE    = var.dynamodb_events_table
            SEND_QUEUE_URL           = var.queues.send_queue_url
            SES_FROM_ADDRESS         = var.ses_from_address
        }
    }
    
    depends_on = [aws_cloudwatch_log_group.ab_test_analyzer]
}

# CloudWatch Log Groups with configurable retention
resource "aws_cloudwatch_log_group" "generate_email" {
    name              = "/aws/lambda/${var.name}-generate-email"
    retention_in_days = local.log_retention_days
}

resource "aws_cloudwatch_log_group" "generate_insights" {
    name              = "/aws/lambda/${var.name}-generate-insights"
    retention_in_days = local.log_retention_days
}

resource "aws_cloudwatch_log_group" "start_campaign" {
    name              = "/aws/lambda/${var.name}-start-campaign"
    retention_in_days = local.log_retention_days
}

resource "aws_cloudwatch_log_group" "send_worker" {
    name              = "/aws/lambda/${var.name}-send-worker"
    retention_in_days = local.log_retention_days
}

resource "aws_cloudwatch_log_group" "tracking_api" {
    name              = "/aws/lambda/${var.name}-tracking-api"
    retention_in_days = local.log_retention_days
}

resource "aws_cloudwatch_log_group" "segments_api" {
    name              = "/aws/lambda/${var.name}-segments-api"
    retention_in_days = local.log_retention_days
}

resource "aws_cloudwatch_log_group" "authorizer" {
    name              = "/aws/lambda/${var.name}-authorizer"
    retention_in_days = local.log_retention_days
}

resource "aws_cloudwatch_log_group" "auth_api" {
    name              = "/aws/lambda/${var.name}-auth-api"
    retention_in_days = local.log_retention_days
}

resource "aws_cloudwatch_log_group" "campaigns_api" {
    name              = "/aws/lambda/${var.name}-campaigns-api"
    retention_in_days = local.log_retention_days
}

resource "aws_cloudwatch_log_group" "ab_test_analyzer" {
    name              = "/aws/lambda/${var.name}-ab-test-analyzer"
    retention_in_days = local.log_retention_days
}


output "start_campaign_arn"   { value = aws_lambda_function.start_campaign.arn }
output "tracking_api_arn"     { value = aws_lambda_function.tracking_api.arn }
output "segments_api_arn"     { value = aws_lambda_function.segments_api.arn }
output "authorizer_arn"       { value = aws_lambda_function.authorizer.invoke_arn }
output "auth_api_arn"         { value = aws_lambda_function.auth_api.arn }
output "campaigns_api_arn"    { value = aws_lambda_function.campaigns_api.arn }
output "generate_email_arn"   { value = aws_lambda_function.generate_email.arn }
output "generate_insights_arn" { value = aws_lambda_function.generate_insights.arn }
output "ab_test_analyzer_arn" { value = aws_lambda_function.ab_test_analyzer.arn }

