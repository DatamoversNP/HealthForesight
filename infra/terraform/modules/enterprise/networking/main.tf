# Private networking skeleton for enterprise landing zone.
# Does NOT create resources unless enable_provision=true (default false).
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.100.0"
    }
  }
}

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

variable "address_space" {
  type    = list(string)
  default = ["10.40.0.0/16"]
}

resource "azurerm_virtual_network" "enterprise" {
  count               = var.enable_provision ? 1 : 0
  name                = "${var.name_prefix}-vnet"
  location            = var.location
  resource_group_name = var.resource_group_name
  address_space       = var.address_space
}

resource "azurerm_subnet" "container_apps" {
  count                = var.enable_provision ? 1 : 0
  name                 = "snet-container-apps"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.enterprise[0].name
  address_prefixes     = ["10.40.1.0/24"]
}

resource "azurerm_subnet" "data" {
  count                = var.enable_provision ? 1 : 0
  name                 = "snet-data"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.enterprise[0].name
  address_prefixes     = ["10.40.2.0/24"]
}

resource "azurerm_subnet" "private_endpoints" {
  count                = var.enable_provision ? 1 : 0
  name                 = "snet-private-endpoints"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.enterprise[0].name
  address_prefixes     = ["10.40.3.0/24"]
}

output "vnet_id" {
  value = try(azurerm_virtual_network.enterprise[0].id, null)
}

output "subnet_container_apps_id" {
  value = try(azurerm_subnet.container_apps[0].id, null)
}
