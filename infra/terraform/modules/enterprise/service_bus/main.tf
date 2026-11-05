# Azure Service Bus — durable dispatch target.
# Default enable_provision=false. Lean: Standard. Full capacity drills: Premium.

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

variable "sku" {
  type        = string
  default     = "Premium"
  description = "Lean staging: Standard. Capacity drills: Premium."

  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.sku)
    error_message = "sku must be Basic, Standard, or Premium."
  }
}

variable "capacity" {
  type        = number
  default     = 1
  description = "Premium messaging units only (ignored for Standard/Basic)."
}

resource "azurerm_servicebus_namespace" "enterprise" {
  count               = var.enable_provision ? 1 : 0
  # Azure forbids namespace names ending in -sb or -mgmt
  name                = "${var.name_prefix}-bus"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = var.sku
  capacity            = var.sku == "Premium" ? var.capacity : 0
}

resource "azurerm_servicebus_queue" "policy_analytics" {
  count        = var.enable_provision ? 1 : 0
  name         = "policy-analytics"
  namespace_id = azurerm_servicebus_namespace.enterprise[0].id

  max_delivery_count                   = 10
  dead_lettering_on_message_expiration = true
  requires_duplicate_detection         = var.sku != "Basic"
  duplicate_detection_history_time_window = var.sku != "Basic" ? "PT10M" : null
  lock_duration                        = "PT1M"
}

resource "azurerm_servicebus_queue" "interactive" {
  count        = var.enable_provision ? 1 : 0
  name         = "interactive"
  namespace_id = azurerm_servicebus_namespace.enterprise[0].id

  max_delivery_count                   = 5
  dead_lettering_on_message_expiration = true
  requires_duplicate_detection         = var.sku != "Basic"
  duplicate_detection_history_time_window = var.sku != "Basic" ? "PT10M" : null
}

output "namespace_id" {
  value = try(azurerm_servicebus_namespace.enterprise[0].id, null)
}

output "namespace_name" {
  value = try(azurerm_servicebus_namespace.enterprise[0].name, null)
}

output "queue_policy_analytics_id" {
  value = try(azurerm_servicebus_queue.policy_analytics[0].id, null)
}

output "sku" {
  value = var.sku
}
