output "api_url" {
    value = module.api.invoke_url
}

output "send_queue_url" {
    value = module.queues.send_queue_url
}
