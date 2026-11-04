# Azure Service Bus Premium — durable dispatch (Celery replacement target).
# Default: no provision (enable_provision=false).

variable "enable_provision" {
  type    = bool
  default = false
}

variable "name_prefix" {
  type = string
}

variable "location" {
  type = string
}

variable "resource_group_name" {
  type = string
}

resource "azurerm_servicebus_namespace" "enterprise" {
  count               = var.enable_provision ? 1 : 0
  name                = "${var.name_prefix}-sb"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "Premium"
  capacity            = 1
  # zone_redundant deprecated in favor of premium messaging units / AZ support by region
}

resource "azurerm_servicebus_queue" "policy_analytics" {
  count        = var.enable_provision ? 1 : 0
  name         = "policy-analytics"
  namespace_id = azurerm_servicebus_namespace.enterprise[0].id

  max_delivery_count               = 10
  dead_lettering_on_message_expiration = true
  requires_duplicate_detection     = true
  duplicate_detection_history_time_window = "PT10M"
  lock_duration                    = "PT1M"
}

resource "azurerm_servicebus_queue" "interactive" {
  count        = var.enable_provision ? 1 : 0
  name         = "interactive"
  namespace_id = azurerm_servicebus_namespace.enterprise[0].id

  max_delivery_count                   = 5
  dead_lettering_on_message_expiration = true
  requires_duplicate_detection         = true
}

output "namespace_id" {
  value = try(azurerm_servicebus_namespace.enterprise[0].id, null)
}

output "queue_policy_analytics_id" {
  value = try(azurerm_servicebus_queue.policy_analytics[0].id, null)
}
