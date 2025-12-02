import {
  to = module.lambdas.aws_cloudwatch_log_group.generate_email
  id = "/aws/lambda/sentinel-generate-email"
}

import {
  to = module.lambdas.aws_cloudwatch_log_group.generate_insights
  id = "/aws/lambda/sentinel-generate-insights"
}

import {
  to = module.lambdas.aws_cloudwatch_log_group.start_campaign
  id = "/aws/lambda/sentinel-start-campaign"
}

import {
  to = module.lambdas.aws_cloudwatch_log_group.send_worker
  id = "/aws/lambda/sentinel-send-worker"
}

import {
  to = module.lambdas.aws_cloudwatch_log_group.tracking_api
  id = "/aws/lambda/sentinel-tracking-api"
}

import {
  to = module.lambdas.aws_cloudwatch_log_group.segments_api
  id = "/aws/lambda/sentinel-segments-api"
}

import {
  to = module.lambdas.aws_cloudwatch_log_group.authorizer
  id = "/aws/lambda/sentinel-authorizer"
}

import {
  to = module.lambdas.aws_cloudwatch_log_group.auth_api
  id = "/aws/lambda/sentinel-auth-api"
}

import {
  to = module.lambdas.aws_cloudwatch_log_group.campaigns_api
  id = "/aws/lambda/sentinel-campaigns-api"
}

import {
  to = module.lambdas.aws_cloudwatch_log_group.ab_test_analyzer
  id = "/aws/lambda/sentinel-ab-test-analyzer"
}
