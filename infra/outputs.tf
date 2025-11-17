output "api_url" {
    value = module.api.invoke_url
}

output "db_arn" {
    value = module.rds.db_arn
}

output "secret_arn" {
    value = module.rds.secret_arn
}

output "send_queue_url" {
    value = module.queues.send_queue_url
}
