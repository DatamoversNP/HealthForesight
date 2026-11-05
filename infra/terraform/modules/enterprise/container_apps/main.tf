# Azure Container Apps — API + workers/Jobs (AKS deferred).
# Default: definitions only (enable_provision=false).

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

variable "subnet_id" {
  type    = string
  default = null
}

variable "log_retention_days" {
  type        = number
  default     = 30
  description = "Lean staging should use short retention (e.g. 7) to control ingestion cost."
}

resource "azurerm_log_analytics_workspace" "aca" {
  count               = var.enable_provision ? 1 : 0
  name                = "${var.name_prefix}-law"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = var.log_retention_days
}

resource "azurerm_container_app_environment" "enterprise" {
  count                      = var.enable_provision ? 1 : 0
  name                       = "${var.name_prefix}-cae"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.aca[0].id
  infrastructure_subnet_id   = var.subnet_id
}

# Placeholder app definitions are intentionally not created until images + Key Vault
# wiring are authorized. Document expected apps:
# - ${name_prefix}-api (ingress external/internal)
# - ${name_prefix}-worker-interactive
# - ${name_prefix}-worker-analytics (or Container Apps Job)

output "environment_id" {
  value = try(azurerm_container_app_environment.enterprise[0].id, null)
}

output "planned_apps" {
  value = [
    "${var.name_prefix}-api",
    "${var.name_prefix}-worker-interactive",
    "${var.name_prefix}-worker-analytics",
  ]
}
