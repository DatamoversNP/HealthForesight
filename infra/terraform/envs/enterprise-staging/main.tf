# Enterprise staging composition — DEFINITIONS ONLY.
# Set enable_provision=true only with explicit authorization (never auto-apply in CI).

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.100.0"
    }
  }
}

provider "azurerm" {
  features {}
}

variable "enable_provision" {
  type        = bool
  default     = false
  description = "MUST remain false unless explicitly authorized to create billable Azure resources."
}

variable "deployment_mode" {
  type        = string
  default     = "saas"
  description = "ADR-005: saas | customer_subscription — same modules, different ownership/identity wiring."

  validation {
    condition     = contains(["saas", "customer_subscription"], var.deployment_mode)
    error_message = "deployment_mode must be saas or customer_subscription."
  }
}

variable "name_prefix" {
  type    = string
  default = "hfentstg"
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
  type        = string
  default     = "healthforesight"
  description = "Human label for bill owner: healthforesight | payer:<code>"
}

module "networking" {
  source              = "../../modules/enterprise/networking"
  enable_provision    = var.enable_provision
  name_prefix         = var.name_prefix
  location            = var.location
  resource_group_name = var.resource_group_name
}

module "service_bus" {
  source              = "../../modules/enterprise/service_bus"
  enable_provision    = var.enable_provision
  name_prefix         = var.name_prefix
  location            = var.location
  resource_group_name = var.resource_group_name
}

module "container_apps" {
  source              = "../../modules/enterprise/container_apps"
  enable_provision    = var.enable_provision
  name_prefix         = var.name_prefix
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = module.networking.subnet_container_apps_id
}

module "postgres_ha" {
  source              = "../../modules/enterprise/postgres_ha"
  enable_provision    = var.enable_provision
  name_prefix         = var.name_prefix
  location            = var.location
  resource_group_name = var.resource_group_name
}

module "adls" {
  source              = "../../modules/enterprise/adls"
  enable_provision    = var.enable_provision
  name_prefix         = var.name_prefix
  location            = var.location
  resource_group_name = var.resource_group_name
}

output "provision_enabled" {
  value = var.enable_provision
}

output "deployment_mode" {
  value = var.deployment_mode
}

output "owner_subscription_label" {
  value = var.owner_subscription_label
}

output "planned_container_apps" {
  value = module.container_apps.planned_apps
}

output "adr_005" {
  value = "Dual mode supported: saas + customer_subscription; core modules shared."
}
