variable "name" {
    type        = string
    description = "Base name/prefix for IAM resources"
}

data "aws_iam_policy_document" "lambda_assume" {
    statement {
        effect  = "Allow"
        actions = ["sts:AssumeRole"]
        principals {
            type        = "Service"
            identifiers = ["lambda.amazonaws.com"]
        }
    }
}

resource "aws_iam_role" "lambda_exec" {
    name               = "${var.name}-lambda-exec"
    assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy" "lambda_policy" {
    name = "${var.name}-lambda-inline"
    role = aws_iam_role.lambda_exec.id
    policy = jsonencode({
        Version = "2012-10-17",
        Statement = [
            { Effect = "Allow", Action = [
                "logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"
            ], Resource = "*" },
            { Effect = "Allow", Action = ["sqs:*"], Resource = "*" },
            { Effect = "Allow", Action = ["ses:*"], Resource = "*" },
            { Effect = "Allow", Action = ["dynamodb:*"], Resource = "*" },
            { Effect = "Allow", Action = ["secretsmanager:GetSecretValue"], Resource = "*" },
            { Effect = "Allow", Action = ["events:Put*","scheduler:*"], Resource = "*" },
            { Effect = "Allow", Action = ["lambda:InvokeFunction"], Resource = "*" },
            { Effect = "Allow", Action = ["iam:PassRole"], Resource = "arn:aws:iam::*:role/*-scheduler-invoke" }
        ]
    })
}

data "aws_iam_policy_document" "scheduler_assume" {
    statement {
        effect  = "Allow"
        actions = ["sts:AssumeRole"]
        principals {
            type        = "Service"
            identifiers = ["scheduler.amazonaws.com"]
        }
    }
}

resource "aws_iam_role" "scheduler_invoke" {
    name               = "${var.name}-scheduler-invoke"
    assume_role_policy = data.aws_iam_policy_document.scheduler_assume.json
}

resource "aws_iam_role_policy" "scheduler_invoke_policy" {
    name = "${var.name}-scheduler-invoke-inline"
    role = aws_iam_role.scheduler_invoke.id
    policy = jsonencode({
        Version = "2012-10-17",
        Statement = [
            { Effect = "Allow", Action = ["lambda:InvokeFunction"], Resource = "*" }
        ]
    })
}

output "roles" {
    value = {
        lambda_exec = aws_iam_role.lambda_exec.arn
    }
}

output "scheduler_invoke_role_arn" {
    value = aws_iam_role.scheduler_invoke.arn
}
