variable "name" {
    type        = string
    description = "Base name/prefix for SQS resources"
}

resource "aws_sqs_queue" "dlq" {
    name = "${var.name}-dlq"
}

resource "aws_sqs_queue" "send_queue" {
    name                       = "${var.name}-send-queue"
    visibility_timeout_seconds = 60
    redrive_policy             = jsonencode({
        deadLetterTargetArn = aws_sqs_queue.dlq.arn,
        maxReceiveCount     = 5
    })
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
