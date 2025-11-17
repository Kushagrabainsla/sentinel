variable "name" { type = string }
variable "engine_version" { type = string }
variable "db_subnet_ids" { type = list(string) }
variable "deletion_protection" { type = bool }
variable "min_capacity" { type = number }
variable "max_capacity" { type = number }

resource "aws_db_subnet_group" "this" {
    name       = "${var.name}-db-subnets"
    subnet_ids = var.db_subnet_ids
}

resource "aws_rds_cluster_parameter_group" "this" {
    name        = "${var.name}-aurora-pg15"
    family      = "aurora-postgresql15"
    description = "${var.name} aurora pg parameter group"
    parameter {
        name = "rds.force_ssl"
        value = "1"
    }
    parameter {
        name = "track_activity_query_size"
        value = "2048" 
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
    serverlessv2_scaling_configuration {
        min_capacity = var.min_capacity
        max_capacity = var.max_capacity
    }
    deletion_protection = var.deletion_protection
}

resource "aws_rds_cluster_instance" "this" {
    identifier         = "${var.name}-aurora-instance-1"
    cluster_identifier = aws_rds_cluster.this.id
    instance_class     = "db.serverless"
    engine             = aws_rds_cluster.this.engine
    engine_version     = aws_rds_cluster.this.engine_version
}

data "aws_secretsmanager_secret" "master" {
    arn = aws_rds_cluster.this.master_user_secret[0].secret_arn
}

output "db_arn" {
    value = aws_rds_cluster.this.arn
}

output "secret_arn" {
    value = data.aws_secretsmanager_secret.master.arn
}
