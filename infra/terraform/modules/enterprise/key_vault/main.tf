# Key Vault + user-assigned managed identity for staging secrets.
# Default enable_provision=false.

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

variable "tenant_id" {
  type = string
}

variable "purge_protection_enabled" {
  type    = bool
  default = false # lean staging: allow purge after destroy; enable for prod
}

resource "azurerm_user_assigned_identity" "staging" {
  count               = var.enable_provision ? 1 : 0
  name                = "${var.name_prefix}-mi"
  location            = var.location
  resource_group_name = var.resource_group_name
}

resource "azurerm_key_vault" "staging" {
  count                       = var.enable_provision ? 1 : 0
  name                        = substr(replace("${var.name_prefix}-kv", "-", ""), 0, 24)
  location                    = var.location
  resource_group_name         = var.resource_group_name
  tenant_id                   = var.tenant_id
  sku_name                    = "standard"
  soft_delete_retention_days  = 7
  purge_protection_enabled    = var.purge_protection_enabled
  rbac_authorization_enabled    = true
  public_network_access_enabled = true
}

output "key_vault_id" {
  value = try(azurerm_key_vault.staging[0].id, null)
}

output "key_vault_uri" {
  value = try(azurerm_key_vault.staging[0].vault_uri, null)
}

output "managed_identity_id" {
  value = try(azurerm_user_assigned_identity.staging[0].id, null)
}

output "managed_identity_principal_id" {
  value = try(azurerm_user_assigned_identity.staging[0].principal_id, null)
}

output "managed_identity_client_id" {
  value = try(azurerm_user_assigned_identity.staging[0].client_id, null)
}
