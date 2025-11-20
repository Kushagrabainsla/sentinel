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

resource "null_resource" "artifacts_dir" {
    provisioner "local-exec" {
        command = "mkdir -p ${path.module}/.artifacts"
    }
}

data "archive_file" "create_campaign" {
    type        = "zip"
    source_dir  = "${path.module}/../../../services/create_campaign"
    output_path = "${path.module}/.artifacts/create_campaign.zip"
    depends_on  = [null_resource.artifacts_dir]
}

data "archive_file" "start_campaign" {
    type        = "zip"
    source_dir  = "${path.module}/../../../services/start_campaign"
    output_path = "${path.module}/.artifacts/start_campaign.zip"
    depends_on  = [null_resource.artifacts_dir]
}

data "archive_file" "send_worker" {
    type        = "zip"
    source_dir  = "${path.module}/../../../services/send_worker"
    output_path = "${path.module}/.artifacts/send_worker.zip"
    depends_on  = [null_resource.artifacts_dir]
}



data "archive_file" "tracking_api" {
    type        = "zip"
    source_dir  = "${path.module}/../../../services/tracking_api"
    output_path = "${path.module}/.artifacts/tracking_api.zip"
    depends_on  = [null_resource.artifacts_dir]
}

data "archive_file" "segments_api" {
    type        = "zip"
    source_dir  = "${path.module}/../../../services/segments_api"
    output_path = "${path.module}/.artifacts/segments_api.zip"
    depends_on  = [null_resource.artifacts_dir]
}

data "archive_file" "authorizer" {
    type        = "zip"
    source_dir  = "${path.module}/../../../services/authorizer"
    output_path = "${path.module}/.artifacts/authorizer.zip"
    depends_on  = [null_resource.artifacts_dir]
}

data "archive_file" "auth_api" {
    type        = "zip"
    source_dir  = "${path.module}/../../../services/auth_api"
    output_path = "${path.module}/.artifacts/auth_api.zip"
    depends_on  = [null_resource.artifacts_dir]
}

data "archive_file" "campaigns_api" {
    type        = "zip"
    source_dir  = "${path.module}/../../../services/campaigns_api"
    output_path = "${path.module}/.artifacts/campaigns_api.zip"
    depends_on  = [null_resource.artifacts_dir]
}

resource "aws_lambda_function" "create_campaign" {
    function_name    = "${var.name}-create-campaign"
    role             = var.roles.lambda_exec
    package_type     = "Zip"
    handler          = "handler.lambda_handler"
    runtime          = "python3.11"
    filename         = data.archive_file.create_campaign.output_path
    source_code_hash = data.archive_file.create_campaign.output_base64sha256
    timeout          = 20
    environment {
        variables = {
            DYNAMODB_CAMPAIGNS_TABLE  = var.dynamodb_campaigns_table
            DYNAMODB_SEGMENTS_TABLE   = var.dynamodb_segments_table
            DYNAMODB_EVENTS_TABLE     = var.dynamodb_events_table
            START_CAMPAIGN_QUEUE_URL  = var.queues.send_queue_url
            START_CAMPAIGN_LAMBDA_ARN = aws_lambda_function.start_campaign.arn
            EVENTBRIDGE_ROLE_ARN      = var.scheduler_invoke_role_arn
        }
    }
}

resource "aws_lambda_function" "start_campaign" {
    function_name    = "${var.name}-start-campaign"
    role             = var.roles.lambda_exec
    handler          = "handler.lambda_handler"
    runtime          = "python3.11"
    filename         = data.archive_file.start_campaign.output_path
    source_code_hash = data.archive_file.start_campaign.output_base64sha256
    timeout          = 60
    environment {
        variables = {
            DYNAMODB_CAMPAIGNS_TABLE  = var.dynamodb_campaigns_table
            DYNAMODB_SEGMENTS_TABLE   = var.dynamodb_segments_table
            DYNAMODB_EVENTS_TABLE     = var.dynamodb_events_table
            SEND_QUEUE_URL = var.queues.send_queue_url
        }
    }
}

resource "aws_lambda_function" "send_worker" {
    function_name    = "${var.name}-send-worker"
    role             = var.roles.lambda_exec
    handler          = "handler.lambda_handler"
    runtime          = "python3.11"
    filename         = data.archive_file.send_worker.output_path
    source_code_hash = data.archive_file.send_worker.output_base64sha256
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
    filename         = data.archive_file.tracking_api.output_path
    source_code_hash = data.archive_file.tracking_api.output_base64sha256
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
    filename         = data.archive_file.segments_api.output_path
    source_code_hash = data.archive_file.segments_api.output_base64sha256
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
    filename         = data.archive_file.authorizer.output_path
    source_code_hash = data.archive_file.authorizer.output_base64sha256
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
    filename         = data.archive_file.auth_api.output_path
    source_code_hash = data.archive_file.auth_api.output_base64sha256
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
    filename         = data.archive_file.campaigns_api.output_path
    source_code_hash = data.archive_file.campaigns_api.output_base64sha256
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

output "create_campaign_arn"  { value = aws_lambda_function.create_campaign.arn }
output "start_campaign_arn"   { value = aws_lambda_function.start_campaign.arn }

output "tracking_api_arn"     { value = aws_lambda_function.tracking_api.arn }
output "segments_api_arn"     { value = aws_lambda_function.segments_api.arn }
output "authorizer_arn"       { value = aws_lambda_function.authorizer.invoke_arn }
output "auth_api_arn"         { value = aws_lambda_function.auth_api.arn }
output "campaigns_api_arn"    { value = aws_lambda_function.campaigns_api.arn }
