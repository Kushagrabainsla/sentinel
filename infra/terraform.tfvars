# Sentinel Infrastructure Configuration
region                  = "us-east-1"
environment             = "prod"

# DynamoDB Configuration
enable_global_tables    = true
global_table_regions    = ["us-east-1", "us-west-2", "eu-west-1"]

# SES Configuration
ses_from_address        = "no-reply@thesentinel.site"
ses_template_name       = "sentinelWrapperTemplate"