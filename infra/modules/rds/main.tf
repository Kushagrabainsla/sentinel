variable "name" { type = string }
variable "engine_version" { type = string }
variable "db_subnet_ids" { type = list(string) }
variable "deletion_protection" { type = bool }
variable "min_capacity" { type = number }
variable "max_capacity" { type = number }
variable "use_serverless_v2" {
    type    = bool
    default = false
}


variable "instance_class" {
    type    = string
    default = "db.t3.medium"
}

variable "free_tier" {
    type    = bool
    default = false
}

variable "instance_master_password" {
    type      = string
    default   = ""
    sensitive = true
}

resource "aws_db_subnet_group" "this" {
    name       = "${var.name}-db-subnets"
    subnet_ids = var.db_subnet_ids
}

resource "aws_rds_cluster_parameter_group" "this" {
    name        = "${var.name}-aurora-pg15"
    family      = "aurora-postgresql15"
    description = "${var.name} aurora pg parameter group"

    parameter {
        name         = "rds.force_ssl"
        value        = "1"
        apply_method = "pending-reboot"
    }

    parameter {
        name         = "track_activity_query_size"
        value        = "2048"
        apply_method = "pending-reboot"
    }
}

resource "aws_rds_cluster" "this" {
    cluster_identifier              = "${var.name}-aurora"
    engine                          = "aurora-postgresql"
    engine_mode                     = "provisioned"
    engine_version                  = var.engine_version
    database_name                   = "sentinel"
    db_subnet_group_name            = aws_db_subnet_group.this.name
    db_cluster_parameter_group_name = aws_rds_cluster_parameter_group.this.name
    manage_master_user_password     = true
    master_username                 = "sentinel_admin"
    enable_http_endpoint            = true
    dynamic "serverlessv2_scaling_configuration" {
        for_each = var.use_serverless_v2 ? [1] : []
        content {
            min_capacity = var.min_capacity
            max_capacity = var.max_capacity
        }
    }
    deletion_protection = var.deletion_protection
}

/*
    Fallback single-instance RDS for free-tier accounts.
    When `var.free_tier` is true we create a Postgres `aws_db_instance` and
    adapt outputs to return its host/port/user. A random password is generated
    when `var.instance_master_password` is not provided.
*/

resource "random_password" "instance" {
    length           = 16
    special          = true
}

resource "aws_db_instance" "this" {
    count               = var.free_tier ? 1 : 0
    identifier          = "${var.name}-instance"
    engine              = "postgres"
    engine_version      = var.engine_version
    instance_class      = var.instance_class
    allocated_storage   = 20
    db_name             = "sentinel"
    username            = "sentinel_admin"
    password            = var.instance_master_password != "" ? var.instance_master_password : random_password.instance.result
    db_subnet_group_name = aws_db_subnet_group.this.name
    deletion_protection = var.deletion_protection
    skip_final_snapshot = true
}

resource "aws_rds_cluster_instance" "this" {
    identifier         = "${var.name}-aurora-instance-1"
    cluster_identifier = aws_rds_cluster.this.id
    instance_class     = var.use_serverless_v2 ? "db.serverless" : var.instance_class
    engine             = aws_rds_cluster.this.engine
    engine_version     = aws_rds_cluster.this.engine_version
}

data "aws_secretsmanager_secret" "master" {
    count = var.free_tier ? 0 : 1
    arn   = aws_rds_cluster.this.master_user_secret[0].secret_arn
}

output "db_address" {
    description = "Primary cluster endpoint for the RDS/Aurora cluster"
    value       = var.free_tier ? aws_db_instance.this[0].address : aws_rds_cluster.this.endpoint
}

output "db_port" {
    description = "Port for the RDS/Aurora cluster"
    value       = var.free_tier ? aws_db_instance.this[0].port : aws_rds_cluster.this.port
}

output "db_name" {
    description = "Database name created in the cluster"
    # aws_rds_cluster has the database_name argument; expose it if present, otherwise fall back to the literal used in the module
    value = var.free_tier ? try(aws_db_instance.this[0].db_name, "sentinel") : try(aws_rds_cluster.this.database_name, "sentinel")
}

output "db_user" {
    description = "Master username for the cluster"
    value       = var.free_tier ? aws_db_instance.this[0].username : aws_rds_cluster.this.master_username
}
