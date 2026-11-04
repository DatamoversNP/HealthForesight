# ADLS Gen2 for landing / curated Delta / results.
# enable_provision=false by default.

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

resource "azurerm_storage_account" "lake" {
  count                    = var.enable_provision ? 1 : 0
  name                     = replace("${var.name_prefix}lake", "-", "")
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "ZRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true
  min_tls_version          = "TLS1_2"
  allow_nested_items_to_be_public = false
}

resource "azurerm_storage_container" "raw" {
  count                 = var.enable_provision ? 1 : 0
  name                  = "raw"
  storage_account_id    = azurerm_storage_account.lake[0].id
  container_access_type = "private"
}

resource "azurerm_storage_container" "curated" {
  count                 = var.enable_provision ? 1 : 0
  name                  = "curated"
  storage_account_id    = azurerm_storage_account.lake[0].id
  container_access_type = "private"
}

resource "azurerm_storage_container" "results" {
  count                 = var.enable_provision ? 1 : 0
  name                  = "results"
  storage_account_id    = azurerm_storage_account.lake[0].id
  container_access_type = "private"
}

output "storage_account_id" {
  value = try(azurerm_storage_account.lake[0].id, null)
}

output "containers" {
  value = ["raw", "curated", "results"]
}
