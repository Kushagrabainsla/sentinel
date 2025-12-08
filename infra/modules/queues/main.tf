variable "name" {
    type        = string
    description = "Base name/prefix for SQS resources"
}

resource "aws_sqs_queue" "dlq" {
    name = "${var.name}-dlq"
    message_retention_seconds = 1209600  # 14 days
}

resource "aws_sqs_queue" "send_queue" {
    name                       = "${var.name}-send-queue"
    visibility_timeout_seconds = 60
    receive_wait_time_seconds  = 20  # Enable long polling
    redrive_policy             = jsonencode({
        deadLetterTargetArn = aws_sqs_queue.dlq.arn,
        maxReceiveCount     = 3  # Reduced from 5 to fail faster
    })
}

# CloudWatch Alarm: Queue Depth Monitoring
resource "aws_cloudwatch_metric_alarm" "queue_depth_high" {
    alarm_name          = "${var.name}-send-queue-depth-high"
    comparison_operator = "GreaterThanThreshold"
    evaluation_periods  = 2
    metric_name         = "ApproximateNumberOfMessagesVisible"
    namespace           = "AWS/SQS"
    period              = 300  # 5 minutes
    statistic           = "Average"
    threshold           = 10000
    alarm_description   = "Alert when SQS queue depth exceeds 10,000 messages"
    treat_missing_data  = "notBreaching"
    
    dimensions = {
        QueueName = aws_sqs_queue.send_queue.name
    }
}

# CloudWatch Alarm: Dead Letter Queue Monitoring
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
    alarm_name          = "${var.name}-dlq-messages-received"
    comparison_operator = "GreaterThanThreshold"
    evaluation_periods  = 1
    metric_name         = "ApproximateNumberOfMessagesVisible"
    namespace           = "AWS/SQS"
    period              = 60  # 1 minute
    statistic           = "Sum"
    threshold           = 0
    alarm_description   = "Alert when messages are sent to DLQ (failed email jobs)"
    treat_missing_data  = "notBreaching"
    
    dimensions = {
        QueueName = aws_sqs_queue.dlq.name
    }
}

output "send_queue_arn" {
    value = aws_sqs_queue.send_queue.arn
}

output "send_queue_url" {
    value = aws_sqs_queue.send_queue.url
}

output "dlq_arn" {
    value = aws_sqs_queue.dlq.arn
}

output "queue_depth_alarm_arn" {
    value = aws_cloudwatch_metric_alarm.queue_depth_high.arn
}

output "dlq_alarm_arn" {
    value = aws_cloudwatch_metric_alarm.dlq_messages.arn
}
