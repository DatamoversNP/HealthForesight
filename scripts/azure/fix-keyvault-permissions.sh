#!/bin/bash
# Fix Key Vault permissions to resolve Terraform purge error

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Key Vault Permissions Fix${NC}"
echo "============================"
echo ""

# Check Azure login
if ! az account show >/dev/null 2>&1; then
    echo -e "${YELLOW}Not logged in to Azure. Please login...${NC}"
    az login
fi

# Get Key Vault name
if [ -z "$KEY_VAULT_NAME" ]; then
    read -p "Enter Key Vault name [uepi-rg-59724-kv]: " KEY_VAULT_NAME
    KEY_VAULT_NAME=${KEY_VAULT_NAME:-uepi-rg-59724-kv}
fi

# Get current user ID
echo -e "${YELLOW}Getting current user ID...${NC}"
CURRENT_USER=$(az ad signed-in-user show --query id -o tsv 2>/dev/null || echo "")

if [ -z "$CURRENT_USER" ]; then
    echo -e "${RED}❌ Could not get current user ID${NC}"
    echo "Please ensure you're logged in with: az login"
    exit 1
fi

echo -e "${GREEN}✅ Current user ID: ${CURRENT_USER}${NC}"

# Check if Key Vault exists
echo ""
echo -e "${YELLOW}Checking Key Vault...${NC}"
if ! az keyvault show --name "${KEY_VAULT_NAME}" >/dev/null 2>&1; then
    echo -e "${RED}❌ Key Vault '${KEY_VAULT_NAME}' not found${NC}"
    echo "Please check the Key Vault name or create it first"
    exit 1
fi

echo -e "${GREEN}✅ Key Vault found: ${KEY_VAULT_NAME}${NC}"

# Add purge permission
echo ""
echo -e "${YELLOW}Adding purge permission to Key Vault...${NC}"
az keyvault set-policy \
  --name "${KEY_VAULT_NAME}" \
  --object-id "${CURRENT_USER}" \
  --secret-permissions get list set delete recover backup restore purge

echo ""
echo -e "${GREEN}✅ Purge permission added successfully!${NC}"
echo ""
echo "You can now retry terraform apply:"
echo "  cd infra/terraform/envs/azure"
echo "  terraform apply"
echo ""

