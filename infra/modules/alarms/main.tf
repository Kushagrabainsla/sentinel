variable "name" { type = string }
variable "lambda_functions" { 
    type = map(object({
        function_name = string
        timeout       = number
    }))
}
variable "dynamodb_tables" { type = list(string) }
variable "api_gateway_id" { type = string }
variable "api_gateway_name" { type = string }
variable "sqs_queue_name" { type = string }
variable "dlq_name" { type = string }

# SNS Topic for alarm notifications
resource "aws_sns_topic" "alarms" {
    name = "${var.name}-alarms"
}

output "sns_topic_arn" {
    value = aws_sns_topic.alarms.arn
}

# Lambda Error Rate Alarms (>5% errors)
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
    for_each = var.lambda_functions
    
    alarm_name          = "${var.name}-${each.key}-error-rate"
    comparison_operator = "GreaterThanThreshold"
    evaluation_periods  = 2
    threshold           = 5
    alarm_description   = "Lambda ${each.key} error rate exceeds 5%"
    treat_missing_data  = "notBreaching"
    
    metric_query {
        id          = "error_rate"
        expression  = "errors / invocations * 100"
        label       = "Error Rate"
        return_data = true
    }
    
    metric_query {
        id = "errors"
        metric {
            namespace   = "AWS/Lambda"
            metric_name = "Errors"
            period      = 300
            stat        = "Sum"
            dimensions = {
                FunctionName = each.value.function_name
            }
        }
    }
    
    metric_query {
        id = "invocations"
        metric {
            namespace   = "AWS/Lambda"
            metric_name = "Invocations"
            period      = 300
            stat        = "Sum"
            dimensions = {
                FunctionName = each.value.function_name
            }
        }
    }
    
    alarm_actions = [aws_sns_topic.alarms.arn]
}

# Lambda Duration Alarms (>80% of timeout)
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
    for_each = var.lambda_functions
    
    alarm_name          = "${var.name}-${each.key}-duration"
    comparison_operator = "GreaterThanThreshold"
    evaluation_periods  = 2
    metric_name         = "Duration"
    namespace           = "AWS/Lambda"
    period              = 300
    statistic           = "Average"
    threshold           = each.value.timeout * 1000 * 0.8  # 80% of timeout in ms
    alarm_description   = "Lambda ${each.key} duration exceeds 80% of timeout"
    treat_missing_data  = "notBreaching"
    
    dimensions = {
        FunctionName = each.value.function_name
    }
    
    alarm_actions = [aws_sns_topic.alarms.arn]
}

# Lambda Throttles Alarm
resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
    for_each = var.lambda_functions
    
    alarm_name          = "${var.name}-${each.key}-throttles"
    comparison_operator = "GreaterThanThreshold"
    evaluation_periods  = 1
    metric_name         = "Throttles"
    namespace           = "AWS/Lambda"
    period              = 60
    statistic           = "Sum"
    threshold           = 0
    alarm_description   = "Lambda ${each.key} is being throttled"
    treat_missing_data  = "notBreaching"
    
    dimensions = {
        FunctionName = each.value.function_name
    }
    
    alarm_actions = [aws_sns_topic.alarms.arn]
}

# DynamoDB Throttling Alarms
resource "aws_cloudwatch_metric_alarm" "dynamodb_read_throttles" {
    for_each = toset(var.dynamodb_tables)
    
    alarm_name          = "${var.name}-${each.key}-read-throttles"
    comparison_operator = "GreaterThanThreshold"
    evaluation_periods  = 1
    metric_name         = "ReadThrottleEvents"
    namespace           = "AWS/DynamoDB"
    period              = 60
    statistic           = "Sum"
    threshold           = 0
    alarm_description   = "DynamoDB table ${each.key} read throttles detected"
    treat_missing_data  = "notBreaching"
    
    dimensions = {
        TableName = each.key
    }
    
    alarm_actions = [aws_sns_topic.alarms.arn]
}

resource "aws_cloudwatch_metric_alarm" "dynamodb_write_throttles" {
    for_each = toset(var.dynamodb_tables)
    
    alarm_name          = "${var.name}-${each.key}-write-throttles"
    comparison_operator = "GreaterThanThreshold"
    evaluation_periods  = 1
    metric_name         = "WriteThrottleEvents"
    namespace           = "AWS/DynamoDB"
    period              = 60
    statistic           = "Sum"
    threshold           = 0
    alarm_description   = "DynamoDB table ${each.key} write throttles detected"
    treat_missing_data  = "notBreaching"
    
    dimensions = {
        TableName = each.key
    }
    
    alarm_actions = [aws_sns_topic.alarms.arn]
}

# API Gateway 5xx Error Alarm
resource "aws_cloudwatch_metric_alarm" "api_gateway_5xx" {
    alarm_name          = "${var.name}-api-5xx-errors"
    comparison_operator = "GreaterThanThreshold"
    evaluation_periods  = 2
    metric_name         = "5XXError"
    namespace           = "AWS/ApiGateway"
    period              = 300
    statistic           = "Sum"
    threshold           = 10
    alarm_description   = "API Gateway 5xx errors exceed threshold"
    treat_missing_data  = "notBreaching"
    
    dimensions = {
        ApiId = var.api_gateway_id
    }
    
    alarm_actions = [aws_sns_topic.alarms.arn]
}

# API Gateway 4xx Error Alarm
resource "aws_cloudwatch_metric_alarm" "api_gateway_4xx" {
    alarm_name          = "${var.name}-api-4xx-errors"
    comparison_operator = "GreaterThanThreshold"
    evaluation_periods  = 2
    metric_name         = "4XXError"
    namespace           = "AWS/ApiGateway"
    period              = 300
    statistic           = "Sum"
    threshold           = 50
    alarm_description   = "API Gateway 4xx errors exceed threshold"
    treat_missing_data  = "notBreaching"
    
    dimensions = {
        ApiId = var.api_gateway_id
    }
    
    alarm_actions = [aws_sns_topic.alarms.arn]
}

# SQS DLQ Messages Alarm (already exists in queues module, but adding here for completeness)
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
    alarm_name          = "${var.name}-dlq-messages"
    comparison_operator = "GreaterThanThreshold"
    evaluation_periods  = 1
    metric_name         = "ApproximateNumberOfMessagesVisible"
    namespace           = "AWS/SQS"
    period              = 60
    statistic           = "Sum"
    threshold           = 0
    alarm_description   = "Messages in DLQ - failed email jobs detected"
    treat_missing_data  = "notBreaching"
    
    dimensions = {
        QueueName = var.dlq_name
    }
    
    alarm_actions = [aws_sns_topic.alarms.arn]
}

# SQS Queue Depth Alarm
resource "aws_cloudwatch_metric_alarm" "queue_depth" {
    alarm_name          = "${var.name}-queue-depth-high"
    comparison_operator = "GreaterThanThreshold"
    evaluation_periods  = 2
    metric_name         = "ApproximateNumberOfMessagesVisible"
    namespace           = "AWS/SQS"
    period              = 300
    statistic           = "Average"
    threshold           = 10000
    alarm_description   = "SQS queue depth exceeds 10,000 messages"
    treat_missing_data  = "notBreaching"
    
    dimensions = {
        QueueName = var.sqs_queue_name
    }
    
    alarm_actions = [aws_sns_topic.alarms.arn]
}
