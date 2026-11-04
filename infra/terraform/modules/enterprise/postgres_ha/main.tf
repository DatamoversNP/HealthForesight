# Azure Database for PostgreSQL Flexible Server — zone-redundant HA target.
# Default enable_provision=false — no billable create without authorization.

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

variable "administrator_login" {
  type    = string
  default = "uepiadmin"
}

variable "administrator_password" {
  type      = string
  sensitive = true
  default   = null
}

resource "azurerm_postgresql_flexible_server" "enterprise" {
  count                  = var.enable_provision ? 1 : 0
  name                   = "${var.name_prefix}-pg"
  resource_group_name    = var.resource_group_name
  location               = var.location
  version                = "15"
  administrator_login    = var.administrator_login
  administrator_password = var.administrator_password
  sku_name               = "GP_Standard_D4s_v3"
  storage_mb             = 131072
  zone                   = "1"
  high_availability {
    mode                      = "ZoneRedundant"
    standby_availability_zone = "2"
  }
}

output "server_fqdn" {
  value = try(azurerm_postgresql_flexible_server.enterprise[0].fqdn, null)
}
