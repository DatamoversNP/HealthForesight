# HEALTHFORESIGHT — LEAN AZURE STAGING (Option B)
# Isolated from healthforesight-rg / Dec4 demo.
#
# THIS FILE DOES NOT AUTHORIZE SPEND.
# enable_provision defaults false. terraform apply requires a separate
# explicit owner approval of the plan + cost package.
#
# Forbidden in this env: PG zone-redundant HA, Service Bus Premium,
# Databricks, Front Door, demo RG modifications, demo DB credentials.

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.100.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.5.0"
    }
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------

variable "enable_provision" {
  type        = bool
  default     = false
  description = "MUST remain false until owner explicitly approves the final plan."
}

variable "deployment_mode" {
  type    = string
  default = "saas"

  validation {
    condition     = contains(["saas", "customer_subscription"], var.deployment_mode)
    error_message = "deployment_mode must be saas or customer_subscription."
  }
}

variable "name_prefix" {
  type    = string
  default = "hfleanstg"
}

variable "location" {
  type    = string
  default = "eastus2"
}

variable "resource_group_name" {
  type    = string
  default = "rg-healthforesight-enterprise-staging"
}

variable "owner_subscription_label" {
  type    = string
  default = "healthforesight"
}

variable "monthly_budget_usd" {
  type        = number
  default     = 400
  description = "Alert threshold (not a hard Azure spend cap)."
}

variable "budget_contact_emails" {
  type        = list(string)
  default     = []
  description = "Emails for budget alerts; empty skips action-group email receivers."
}

variable "postgres_sku_name" {
  type    = string
  default = "B_Standard_B2s"
}

variable "postgres_storage_mb" {
  type    = number
  default = 32768
}

variable "service_bus_sku" {
  type    = string
  default = "Standard"
}

variable "adls_replication_type" {
  type    = string
  default = "LRS"
}

variable "vnet_address_space" {
  type    = list(string)
  default = ["10.50.0.0/16"] # distinct from any demo/default 10.40/10.0 spaces
}

variable "log_retention_days" {
  type        = number
  default     = 30
  description = "Log Analytics minimum retention is 30 days on current Azure SKU."
}

variable "create_container_apps_environment" {
  type        = bool
  default     = true
  description = "LAW + ACA environment only; no API/worker apps until second authorization."
}

variable "tags" {
  type = map(string)
  default = {
    purpose            = "enterprise-lean-staging"
    demo_isolation     = "absolute"
    cost_center        = "healthforesight-engineering"
    review_after_days  = "14"
    budget_alert_usd   = "400"
    do_not_touch_demo  = "healthforesight-rg"
  }
}

data "azurerm_client_config" "current" {}

# ---------------------------------------------------------------------------
# Resource group — NEW only; never healthforesight-rg
# ---------------------------------------------------------------------------

resource "azurerm_resource_group" "lean" {
  count    = var.enable_provision ? 1 : 0
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags

  lifecycle {
    precondition {
      condition     = var.resource_group_name != "healthforesight-rg"
      error_message = "Refusing to target demo resource group healthforesight-rg."
    }
  }
}

locals {
  rg_name = var.enable_provision ? azurerm_resource_group.lean[0].name : var.resource_group_name
  # Password never reused from demo — generated only when provisioning.
  postgres_admin_password = var.enable_provision ? random_password.pg[0].result : null
}

resource "random_password" "pg" {
  count            = var.enable_provision ? 1 : 0
  length           = 32
  special          = true
  override_special = "!@#%^*-_=+"
}

# ---------------------------------------------------------------------------
# Modules (lean SKUs)
# ---------------------------------------------------------------------------

module "networking" {
  source              = "../../modules/enterprise/networking"
  enable_provision    = var.enable_provision
  name_prefix         = var.name_prefix
  location            = var.location
  resource_group_name = local.rg_name
  address_space       = var.vnet_address_space

  depends_on = [azurerm_resource_group.lean]
}

module "key_vault" {
  source              = "../../modules/enterprise/key_vault"
  enable_provision    = var.enable_provision
  name_prefix         = var.name_prefix
  location            = var.location
  resource_group_name = local.rg_name
  tenant_id           = data.azurerm_client_config.current.tenant_id

  depends_on = [azurerm_resource_group.lean]
}

module "postgres" {
  source                        = "../../modules/enterprise/postgres_ha"
  enable_provision              = var.enable_provision
  name_prefix                   = var.name_prefix
  location                      = var.location
  resource_group_name           = local.rg_name
  administrator_login           = "hfleanadmin"
  administrator_password        = local.postgres_admin_password
  sku_name                      = var.postgres_sku_name
  storage_mb                    = var.postgres_storage_mb
  enable_zone_redundant_ha      = false
  public_network_access_enabled = true
  backup_retention_days         = 7

  depends_on = [azurerm_resource_group.lean]
}

module "service_bus" {
  source              = "../../modules/enterprise/service_bus"
  enable_provision    = var.enable_provision
  name_prefix         = var.name_prefix
  location            = var.location
  resource_group_name = local.rg_name
  sku                 = var.service_bus_sku

  depends_on = [azurerm_resource_group.lean]
}

module "adls" {
  source              = "../../modules/enterprise/adls"
  enable_provision    = var.enable_provision
  name_prefix         = var.name_prefix
  location            = var.location
  resource_group_name = local.rg_name
  replication_type    = var.adls_replication_type

  depends_on = [azurerm_resource_group.lean]
}

module "container_apps" {
  source              = "../../modules/enterprise/container_apps"
  enable_provision    = var.enable_provision && var.create_container_apps_environment
  name_prefix         = var.name_prefix
  location            = var.location
  resource_group_name = local.rg_name
  subnet_id           = module.networking.subnet_container_apps_id
  log_retention_days  = var.log_retention_days

  depends_on = [azurerm_resource_group.lean, module.networking]
}

# Store generated PG password in Key Vault (staging-only secret — never demo KV).
resource "azurerm_role_assignment" "kv_secrets_officer_deployer" {
  count                = var.enable_provision ? 1 : 0
  scope                = module.key_vault.key_vault_id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_key_vault_secret" "pg_password" {
  count        = var.enable_provision ? 1 : 0
  name         = "lean-staging-pg-admin-password"
  value        = local.postgres_admin_password
  key_vault_id = module.key_vault.key_vault_id

  depends_on = [azurerm_role_assignment.kv_secrets_officer_deployer]
}

resource "azurerm_key_vault_secret" "pg_fqdn" {
  count        = var.enable_provision ? 1 : 0
  name         = "lean-staging-pg-fqdn"
  value        = coalesce(module.postgres.server_fqdn, "pending")
  key_vault_id = module.key_vault.key_vault_id

  depends_on = [azurerm_role_assignment.kv_secrets_officer_deployer, module.postgres]
}

# ---------------------------------------------------------------------------
# Budget alert (soft ceiling — not a hard Azure hard-cap)
# ---------------------------------------------------------------------------

resource "azurerm_monitor_action_group" "budget" {
  count               = var.enable_provision && length(var.budget_contact_emails) > 0 ? 1 : 0
  name                = "${var.name_prefix}-budget-ag"
  resource_group_name = local.rg_name
  short_name          = "hfleanbud"

  dynamic "email_receiver" {
    for_each = var.budget_contact_emails
    content {
      name          = "owner-${email_receiver.key}"
      email_address = email_receiver.value
    }
  }
}

resource "azurerm_consumption_budget_resource_group" "lean" {
  count             = var.enable_provision ? 1 : 0
  name              = "${var.name_prefix}-budget-400"
  resource_group_id = azurerm_resource_group.lean[0].id

  amount     = var.monthly_budget_usd
  time_grain = "Monthly"

  time_period {
    start_date = formatdate("YYYY-MM-01'T'00:00:00Z", timestamp())
  }

  notification {
    enabled        = true
    threshold      = 80.0
    operator       = "GreaterThan"
    threshold_type = "Actual"
    contact_emails = length(var.budget_contact_emails) > 0 ? var.budget_contact_emails : null
    contact_roles  = length(var.budget_contact_emails) > 0 ? null : ["Owner"]
  }

  notification {
    enabled        = true
    threshold      = 100.0
    operator       = "GreaterThan"
    threshold_type = "Forecasted"
    contact_emails = length(var.budget_contact_emails) > 0 ? var.budget_contact_emails : null
    contact_roles  = length(var.budget_contact_emails) > 0 ? null : ["Owner"]
  }

  lifecycle {
    ignore_changes = [time_period]
  }
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

output "provision_enabled" {
  value = var.enable_provision
}

output "subscription_id" {
  value = data.azurerm_client_config.current.subscription_id
}

output "tenant_id" {
  value = data.azurerm_client_config.current.tenant_id
}

output "resource_group_name" {
  value = var.resource_group_name
}

output "demo_isolation" {
  value = {
    forbidden_rg           = "healthforesight-rg"
    staging_rg             = var.resource_group_name
    postgres_ha            = false
    service_bus_sku        = var.service_bus_sku
    postgres_sku           = var.postgres_sku_name
    databricks             = false
    front_door             = false
    shares_demo_credentials = false
    synthetic_data_only    = true
  }
}

output "postgres_fqdn" {
  value = module.postgres.server_fqdn
}

output "service_bus_sku" {
  value = module.service_bus.sku
}

output "key_vault_uri" {
  value = module.key_vault.key_vault_uri
}

output "adls_account" {
  value = module.adls.storage_account_name
}

output "planned_container_apps" {
  value = module.container_apps.planned_apps
}

output "teardown_command" {
  value = "cd infra/terraform/envs/enterprise-lean-staging && terraform destroy -var='enable_provision=true' -auto-approve"
}

output "adr_note" {
  value = "Lean staging validates install/dispatch/schedule isolation before Premium/HA spend."
}
