variable "environment" {
    type        = string
    default     = "prod"
    description = "Fixed environment name"
}

variable "region" {
    type = string
}

variable "enable_global_tables" {
    type        = bool
    default     = false
    description = "Enable DynamoDB global tables across regions"
}

variable "global_table_regions" {
    type        = list(string)
    default     = []
    description = "List of regions for DynamoDB global tables"
}

variable "ses_from_address" {
    type = string
}

variable "frontend_url" {
    type        = string
    default     = "https://dashboard.thesentinel.site"
    description = "Public dashboard URL used in account verification links"
}
