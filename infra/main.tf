terraform {
    required_version = ">= 1.6"
    required_providers {
        aws     = { source = "hashicorp/aws",     version = "~> 5.62" }
        archive = { source = "hashicorp/archive", version = "~> 2.5" }
    }
}

provider "aws" {
    region = var.region
}

locals {
    project = "sentinel"
    env     = var.environment
    name    = "${local.project}-${local.env}"
}

# IAM
module "iam" {
    source = "./modules/iam"
    name   = local.name
}

# Queues
module "queues" {
    source = "./modules/queues"
    name   = local.name
}

# RDS Aurora Serverless v2
module "rds" {
    source              = "./modules/rds"
    name                = local.name
    engine_version      = var.db_engine_version
    db_subnet_ids       = var.db_subnet_ids
    deletion_protection = var.db_deletion_protection
    min_capacity        = var.db_min_capacity
    max_capacity        = var.db_max_capacity
}

# Lambdas
module "lambdas" {
    source            = "./modules/lambdas"
    name              = local.name
    region            = var.region
    roles             = module.iam.roles
    queues            = module.queues
    db_arn            = module.rds.db_arn
    secret_arn        = module.rds.secret_arn
    ses_from_address  = var.ses_from_address
    ses_template_name = var.ses_template_name
}

# API Gateway
module "api" {
    source              = "./modules/api"
    name                = local.name
    create_campaign_arn = module.lambdas.create_campaign_arn
}

# Events (SES webhooks + Scheduler)
module "events" {
    source                         = "./modules/events"
    name                           = local.name
    start_campaign_lambda_arn      = module.lambdas.start_campaign_arn
    start_campaign_invoke_role_arn = module.iam.scheduler_invoke_role_arn
    ses_events_lambda_arn          = module.lambdas.event_normalizer_arn
}

output "api_url" {
    value = module.api.invoke_url
}
