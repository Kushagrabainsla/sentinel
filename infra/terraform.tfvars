region                  = "us-east-1"
environment             = "prod"

# Replace with your private subnet IDs
db_subnet_ids           = ["subnet-aaa111", "subnet-bbb222", "subnet-ccc333"]

db_engine_version       = "15.4"
db_min_capacity         = 0.5
db_max_capacity         = 2.0
db_deletion_protection  = false

ses_from_address        = "no-reply@yourdomain.com"
ses_template_name       = "DefaultTemplate"
