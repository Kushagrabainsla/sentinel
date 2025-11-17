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

variable "with_express_configuration" {
    type    = bool
    default = false
}

variable "instance_class" {
    type    = string
    default = "db.t3.medium"
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
    # When running in AWS free-tier accounts, the RDS API requires the
    # WithExpressConfiguration flag to be set. Expose a toggle variable so
    # callers can enable it (set to true in free-tier accounts).
    with_express_configuration     = var.with_express_configuration
    dynamic "serverlessv2_scaling_configuration" {
        for_each = var.use_serverless_v2 ? [1] : []
        content {
            min_capacity = var.min_capacity
            max_capacity = var.max_capacity
        }
    }
    deletion_protection = var.deletion_protection
}

resource "aws_rds_cluster_instance" "this" {
    identifier         = "${var.name}-aurora-instance-1"
    cluster_identifier = aws_rds_cluster.this.id
    instance_class     = var.use_serverless_v2 ? "db.serverless" : var.instance_class
    engine             = aws_rds_cluster.this.engine
    engine_version     = aws_rds_cluster.this.engine_version
}

data "aws_secretsmanager_secret" "master" {
    arn = aws_rds_cluster.this.master_user_secret[0].secret_arn
}

output "db_address" {
    description = "Primary cluster endpoint for the RDS/Aurora cluster"
    value       = aws_rds_cluster.this.endpoint
}

output "db_port" {
    description = "Port for the RDS/Aurora cluster"
    value       = aws_rds_cluster.this.port
}

output "db_name" {
    description = "Database name created in the cluster"
    # aws_rds_cluster has the database_name argument; expose it if present, otherwise fall back to the literal used in the module
    value = try(aws_rds_cluster.this.database_name, "sentinel")
}

output "db_user" {
    description = "Master username for the cluster"
    value       = aws_rds_cluster.this.master_username
}
