variable "environment" {
    type    = string
    default = "prod"
}

variable "region" {
    type = string
}

variable "db_password" {
    type      = string
    sensitive = true
}

variable "db_engine_version" {
    type    = string
    default = "15.4"
}

variable "db_min_capacity" {
    type    = number
    default = 0.5
}

variable "db_max_capacity" {
    type    = number
    default = 2.0
}

variable "db_deletion_protection" {
    type    = bool
    default = false
}

variable "ses_from_address" {
    type = string
}

variable "ses_template_name" {
    type    = string
    default = "sentinelWrapperTemplate"
}
