variable "name"              { type = string }
variable "region"            { type = string }
variable "roles"             { type = any }
variable "queues"            { type = any }
variable "db_arn"            { type = string }
variable "secret_arn"        { type = string }
variable "ses_from_address"  { type = string }
variable "ses_template_name" { type = string }

resource "null_resource" "artifacts_dir" {
    provisioner "local-exec" {
        command = "mkdir -p ${path.module}/.artifacts"
    }
}

data "archive_file" "create_campaign" {
    type        = "zip"
    source_dir  = "${path.module}/../../../lambdas/create_campaign"
    output_path = "${path.module}/.artifacts/create_campaign.zip"
    depends_on  = [null_resource.artifacts_dir]
}

data "archive_file" "start_campaign" {
    type        = "zip"
    source_dir  = "${path.module}/../../../lambdas/start_campaign"
    output_path = "${path.module}/.artifacts/start_campaign.zip"
    depends_on  = [null_resource.artifacts_dir]
}

data "archive_file" "send_worker" {
    type        = "zip"
    source_dir  = "${path.module}/../../../lambdas/send_worker"
    output_path = "${path.module}/.artifacts/send_worker.zip"
    depends_on  = [null_resource.artifacts_dir]
}

data "archive_file" "event_normalizer" {
    type        = "zip"
    source_dir  = "${path.module}/../../../lambdas/event_normalizer"
    output_path = "${path.module}/.artifacts/event_normalizer.zip"
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
            DB_ARN                    = var.db_arn
            SECRET_ARN                = var.secret_arn
            START_CAMPAIGN_QUEUE_URL  = var.queues.send_queue_url
            START_CAMPAIGN_LAMBDA_ARN = aws_lambda_function.start_campaign.arn
            EVENTBRIDGE_ROLE_ARN      = ""
            AWS_REGION                = var.region
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
            DB_ARN         = var.db_arn
            SECRET_ARN     = var.secret_arn
            SEND_QUEUE_URL = var.queues.send_queue_url
            AWS_REGION     = var.region
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
            DB_ARN            = var.db_arn
            SECRET_ARN        = var.secret_arn
            SES_FROM_ADDRESS  = var.ses_from_address
            SES_TEMPLATE_ARN  = var.ses_template_name
            AWS_REGION        = var.region
        }
    }
}

resource "aws_lambda_event_source_mapping" "send_worker_sqs" {
    event_source_arn = var.queues.send_queue_arn
    function_name    = aws_lambda_function.send_worker.arn
    batch_size       = 10
}

resource "aws_lambda_function" "event_normalizer" {
    function_name    = "${var.name}-event-normalizer"
    role             = var.roles.lambda_exec
    handler          = "handler.lambda_handler"
    runtime          = "python3.11"
    filename         = data.archive_file.event_normalizer.output_path
    source_code_hash = data.archive_file.event_normalizer.output_base64sha256
    timeout          = 20
    environment {
        variables = {
            DB_ARN     = var.db_arn
            SECRET_ARN = var.secret_arn
            AWS_REGION = var.region
        }
    }
}

output "create_campaign_arn"  { value = aws_lambda_function.create_campaign.arn }
output "start_campaign_arn"   { value = aws_lambda_function.start_campaign.arn }
output "event_normalizer_arn" { value = aws_lambda_function.event_normalizer.arn }
