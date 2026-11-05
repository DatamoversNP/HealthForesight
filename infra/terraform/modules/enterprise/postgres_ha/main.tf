# Azure Database for PostgreSQL Flexible Server.
# Default enable_provision=false — no billable create without authorization.
# Lean staging: small single-AZ SKU. Full enterprise: GP + zone-redundant HA.

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

variable "sku_name" {
  type        = string
  default     = "GP_Standard_D4s_v3"
  description = "Lean: B_Standard_B2s or GP_Standard_D2s_v3. Full: GP_Standard_D4s_v3+."
}

variable "storage_mb" {
  type    = number
  default = 131072
}

variable "postgres_version" {
  type    = string
  default = "15"
}

variable "enable_zone_redundant_ha" {
  type        = bool
  default     = true
  description = "Lean staging MUST set false (single-AZ). Full HA drills set true."
}

variable "public_network_access_enabled" {
  type    = bool
  default = true
}

variable "backup_retention_days" {
  type    = number
  default = 7
}

resource "azurerm_postgresql_flexible_server" "enterprise" {
  count                  = var.enable_provision ? 1 : 0
  name                   = "${var.name_prefix}-pg"
  resource_group_name    = var.resource_group_name
  location               = var.location
  version                = var.postgres_version
  administrator_login    = var.administrator_login
  administrator_password = var.administrator_password
  sku_name               = var.sku_name
  storage_mb             = var.storage_mb
  zone                   = "1"
  public_network_access_enabled = var.public_network_access_enabled
  backup_retention_days  = var.backup_retention_days

  dynamic "high_availability" {
    for_each = var.enable_zone_redundant_ha ? [1] : []
    content {
      mode                      = "ZoneRedundant"
      standby_availability_zone = "2"
    }
  }

  lifecycle {
    prevent_destroy = false
  }
}

# Allow Azure services to reach lean public endpoint (staging only; tighten later).
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure" {
  count            = var.enable_provision && var.public_network_access_enabled ? 1 : 0
  name             = "AllowAzureServices"
  server_id        = azurerm_postgresql_flexible_server.enterprise[0].id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

output "server_fqdn" {
  value = try(azurerm_postgresql_flexible_server.enterprise[0].fqdn, null)
}

output "server_id" {
  value = try(azurerm_postgresql_flexible_server.enterprise[0].id, null)
}

output "sku_name" {
  value = var.sku_name
}

output "zone_redundant_ha" {
  value = var.enable_zone_redundant_ha
}
