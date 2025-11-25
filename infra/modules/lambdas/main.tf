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




resource "aws_lambda_function" "generate_email" {
    function_name    = "${var.name}-generate-email"
    role             = var.roles.lambda_exec
    handler          = "handler.lambda_handler"
    runtime          = "python3.11"
    filename         = "${path.module}/.artifacts/generate_email.zip"
    source_code_hash = filebase64sha256("${path.module}/.artifacts/generate_email.zip")
    timeout          = 30
    environment {
        variables = {}
    }
}

resource "aws_lambda_function" "generate_insights" {
    function_name    = "${var.name}-generate-insights"
    role             = var.roles.lambda_exec
    handler          = "handler.lambda_handler"
    runtime          = "python3.11"
    filename         = "${path.module}/.artifacts/generate_insights.zip"
    source_code_hash = filebase64sha256("${path.module}/.artifacts/generate_insights.zip")
    timeout          = 60
    environment {
        variables = {}
    }
}


resource "aws_lambda_function" "start_campaign" {
    function_name    = "${var.name}-start-campaign"
    role             = var.roles.lambda_exec
    handler          = "handler.lambda_handler"
    runtime          = "python3.11"
    filename         = "${path.module}/.artifacts/start_campaign.zip"
    source_code_hash = filebase64sha256("${path.module}/.artifacts/start_campaign.zip")
    timeout          = 60
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
}

resource "aws_lambda_function" "send_worker" {
    function_name    = "${var.name}-send-worker"
    role             = var.roles.lambda_exec
    handler          = "handler.lambda_handler"
    runtime          = "python3.11"
    filename         = "${path.module}/.artifacts/send_worker.zip"
    source_code_hash = filebase64sha256("${path.module}/.artifacts/send_worker.zip")
    timeout          = 60
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
}

resource "aws_lambda_event_source_mapping" "send_worker_sqs" {
    event_source_arn = var.queues.send_queue_arn
    function_name    = aws_lambda_function.send_worker.arn
    batch_size       = 10
}



resource "aws_lambda_function" "tracking_api" {
    function_name    = "${var.name}-tracking-api"
    role             = var.roles.lambda_exec
    handler          = "handler.lambda_handler"
    runtime          = "python3.11"
    filename         = "${path.module}/.artifacts/tracking_api.zip"
    source_code_hash = filebase64sha256("${path.module}/.artifacts/tracking_api.zip")
    timeout          = 30
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
}

resource "aws_lambda_function" "segments_api" {
    function_name    = "${var.name}-segments-api"
    role             = var.roles.lambda_exec
    handler          = "handler.lambda_handler"
    runtime          = "python3.11"
    filename         = "${path.module}/.artifacts/segments_api.zip"
    source_code_hash = filebase64sha256("${path.module}/.artifacts/segments_api.zip")
    timeout          = 30
    environment {
        variables = {
            DYNAMODB_CAMPAIGNS_TABLE = var.dynamodb_campaigns_table
            DYNAMODB_SEGMENTS_TABLE  = var.dynamodb_segments_table
            DYNAMODB_EVENTS_TABLE    = var.dynamodb_events_table
        }
    }
}

resource "aws_lambda_function" "authorizer" {
    function_name    = "${var.name}-authorizer"
    role             = var.roles.lambda_exec
    handler          = "handler.lambda_handler"
    runtime          = "python3.11"
    filename         = "${path.module}/.artifacts/authorizer.zip"
    source_code_hash = filebase64sha256("${path.module}/.artifacts/authorizer.zip")
    timeout          = 10
    environment {
        variables = {
            DYNAMODB_USERS_TABLE = var.dynamodb_users_table
        }
    }
}

resource "aws_lambda_function" "auth_api" {
    function_name    = "${var.name}-auth-api"
    role             = var.roles.lambda_exec
    handler          = "handler.lambda_handler"
    runtime          = "python3.11"
    filename         = "${path.module}/.artifacts/auth_api.zip"
    source_code_hash = filebase64sha256("${path.module}/.artifacts/auth_api.zip")
    timeout          = 30
    environment {
        variables = {
            DYNAMODB_USERS_TABLE = var.dynamodb_users_table
        }
    }
}

resource "aws_lambda_function" "campaigns_api" {
    function_name    = "${var.name}-campaigns-api"
    role             = var.roles.lambda_exec
    handler          = "handler.lambda_handler"
    runtime          = "python3.11"
    filename         = "${path.module}/.artifacts/campaigns_api.zip"
    source_code_hash = filebase64sha256("${path.module}/.artifacts/campaigns_api.zip")
    timeout          = 30
    environment {
        variables = {
            DYNAMODB_CAMPAIGNS_TABLE     = var.dynamodb_campaigns_table
            DYNAMODB_SEGMENTS_TABLE      = var.dynamodb_segments_table
            DYNAMODB_EVENTS_TABLE        = var.dynamodb_events_table
            START_CAMPAIGN_LAMBDA_ARN    = aws_lambda_function.start_campaign.arn
            EVENTBRIDGE_ROLE_ARN         = var.scheduler_invoke_role_arn
        }
    }
}

resource "aws_lambda_function" "ab_test_analyzer" {
    function_name    = "${var.name}-ab-test-analyzer"
    role             = var.roles.lambda_exec
    handler          = "handler.lambda_handler"
    runtime          = "python3.11"
    filename         = "${path.module}/.artifacts/ab_test_analyzer.zip"
    source_code_hash = filebase64sha256("${path.module}/.artifacts/ab_test_analyzer.zip")
    timeout          = 60
    environment {
        variables = {
            DYNAMODB_CAMPAIGNS_TABLE = var.dynamodb_campaigns_table
            DYNAMODB_SEGMENTS_TABLE  = var.dynamodb_segments_table
            DYNAMODB_EVENTS_TABLE    = var.dynamodb_events_table
            SEND_QUEUE_URL           = var.queues.send_queue_url
            SES_FROM_ADDRESS         = var.ses_from_address
        }
    }
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

