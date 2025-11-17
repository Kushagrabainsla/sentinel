variable "name" { type = string }
variable "start_campaign_lambda_arn" { type = string }
variable "start_campaign_invoke_role_arn" { type = string }
variable "ses_events_lambda_arn" { type = string }

resource "aws_sns_topic" "ses_events" {
    name = "${var.name}-ses-events"
}

resource "aws_sns_topic_subscription" "ses_events_lambda" {
    topic_arn = aws_sns_topic.ses_events.arn
    protocol  = "lambda"
    endpoint  = var.ses_events_lambda_arn
}

resource "aws_lambda_permission" "allow_sns" {
    statement_id  = "AllowSNSToInvokeLambda"
    action        = "lambda:InvokeFunction"
    function_name = var.ses_events_lambda_arn
    principal     = "sns.amazonaws.com"
    source_arn    = aws_sns_topic.ses_events.arn
}

output "ses_topic_arn" {
    value = aws_sns_topic.ses_events.arn
}
