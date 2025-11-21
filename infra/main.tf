terraform {
    required_version = ">= 1.6"
    required_providers {
        aws     = { source = "hashicorp/aws",     version = "~> 5.62" }
        archive = { source = "hashicorp/archive", version = "~> 2.5" }
    }
    
    backend "s3" {
        bucket = "sentinel-terraform-state-us-east-1"  # Use a unique bucket name
        key    = "infra/terraform.tfstate"
        region = "us-east-1"
    }
}

provider "aws" {
    region = var.region
}

locals {
    project = "sentinel"
    name    = "sentinel"
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

# Networking (new)
module "network" {
    source = "./modules/network"
    name   = local.name
}

# DynamoDB
module "dynamodb" {
    source                = "./modules/dynamodb"
    name                  = local.name
    enable_global_tables  = var.enable_global_tables
    global_table_regions  = var.global_table_regions
}

# Lambdas
module "lambdas" {
    source            = "./modules/lambdas"
    name              = local.name
    region            = var.region
    roles             = module.iam.roles
    queues            = module.queues
    
    # DynamoDB tables
    dynamodb_users_table         = module.dynamodb.users_table
    dynamodb_campaigns_table     = module.dynamodb.campaigns_table
    dynamodb_segments_table      = module.dynamodb.segments_table
    dynamodb_events_table        = module.dynamodb.events_table
    dynamodb_link_mappings_table = module.dynamodb.link_mappings_table
    
    ses_from_address          = var.ses_from_address
    scheduler_invoke_role_arn = module.iam.scheduler_invoke_role_arn
    tracking_base_url         = module.api.custom_domain_url
    assets_bucket_name        = module.s3_assets.bucket_name
    sentinel_logo_url         = module.s3_assets.sentinel_logo_url
}

# SES Configuration with DKIM
module "ses" {
    source = "./modules/ses"
    domain = "thesentinel.site"
}

# S3 Assets Bucket
module "s3_assets" {
    source = "./modules/s3_assets"
    name   = local.name
}

# API Gateway
module "api" {
    source                          = "./modules/api"
    name                            = local.name
    tracking_api_arn                = module.lambdas.tracking_api_arn
    segments_api_arn                = module.lambdas.segments_api_arn
    authorizer_arn                  = module.lambdas.authorizer_arn
    auth_api_arn                    = module.lambdas.auth_api_arn
    campaigns_api_arn               = module.lambdas.campaigns_api_arn
    generate_email_lambda_arn       = module.lambdas.generate_email_arn
}

# Events (EventBridge Scheduler only - SES events not configured)
# module "events" {
#     source                         = "./modules/events"
#     name                           = local.name
#     start_campaign_lambda_arn      = module.lambdas.start_campaign_arn
#     start_campaign_invoke_role_arn = module.iam.scheduler_invoke_role_arn
#     ses_events_lambda_arn          = module.lambdas.event_normalizer_arn
# }
