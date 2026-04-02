#!/usr/bin/env bash
# Provision a fresh HealthForesight v3 deployment on Azure.
# Uses a separate resource group and app names so the existing deployment is NOT disturbed.
# Run from repo root: ./scripts/azure/provision-fresh-v3.sh

set -e

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-v3-rg}"
LOCATION="${LOCATION:-eastus}"
APP_SERVICE_PLAN="${APP_SERVICE_PLAN:-healthforesight-v3-plan}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-v3}"
STATIC_WEB_APP_NAME="${STATIC_WEB_APP_NAME:-healthforesight-web-v3}"
STORAGE_ACCOUNT_NAME="${STORAGE_ACCOUNT_NAME:-hfv3storage$(date +%s | tail -c 6)}"
FILE_SHARE_NAME="${FILE_SHARE_NAME:-healthforesight-data}"

echo "=============================================="
echo "HealthForesight v3 – Fresh Azure provisioning"
echo "=============================================="
echo ""
echo "Resource group:    $RESOURCE_GROUP"
echo "API app name:      $API_APP_NAME"
echo "Static web name:   $STATIC_WEB_APP_NAME"
echo "Location:          $LOCATION"
echo ""
echo "Existing deployment (healthforesight-rg / *-9016) is NOT modified."
echo ""

if ! command -v az &>/dev/null; then
  echo "Azure CLI is not installed. Install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
  exit 1
fi

if ! az account show &>/dev/null; then
  echo "Logging in to Azure..."
  az login
fi

echo "Creating resource group..."
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --output none

echo "Creating storage account and file share..."
az storage account create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$STORAGE_ACCOUNT_NAME" \
  --location "$LOCATION" \
  --sku Standard_LRS \
  --kind StorageV2 \
  --output none

STORAGE_KEY=$(az storage account keys list \
  --resource-group "$RESOURCE_GROUP" \
  --account-name "$STORAGE_ACCOUNT_NAME" \
  --query "[0].value" -o tsv)

az storage share create \
  --account-name "$STORAGE_ACCOUNT_NAME" \
  --account-key "$STORAGE_KEY" \
  --name "$FILE_SHARE_NAME" \
  --quota 100 \
  --output none

echo "Creating App Service plan (Linux, B1)..."
az appservice plan create \
  --name "$APP_SERVICE_PLAN" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku B1 \
  --is-linux \
  --output none

echo "Creating Web App for API (Python 3.11)..."
az webapp create \
  --resource-group "$RESOURCE_GROUP" \
  --plan "$APP_SERVICE_PLAN" \
  --name "$API_APP_NAME" \
  --runtime "PYTHON:3.11" \
  --output none

echo "Configuring API app settings..."
az webapp config appsettings set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$API_APP_NAME" \
  --settings \
    USE_AZURE_FILE_STORAGE=true \
    AZURE_STORAGE_ACCOUNT_NAME="$STORAGE_ACCOUNT_NAME" \
    AZURE_STORAGE_FILE_SHARE_NAME=$FILE_SHARE_NAME \
    AZURE_STORAGE_ACCOUNT_KEY="$STORAGE_KEY" \
    ENVIRONMENT=production \
    USE_FILE_STORAGE=true \
    CORS_ORIGINS="https://$STATIC_WEB_APP_NAME.azurestaticapps.net,https://$API_APP_NAME.azurewebsites.net" \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none

az webapp config set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$API_APP_NAME" \
  --startup-file "startup.sh" \
  --output none

echo "Creating Static Web App for frontend..."
STATIC_LOCATION="$LOCATION"
[[ "$LOCATION" == "eastus" ]] && STATIC_LOCATION="eastus2"
az staticwebapp create \
  --name "$STATIC_WEB_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$STATIC_LOCATION" \
  --sku Free \
  --output none

echo ""
echo "=============================================="
echo "Provisioning complete"
echo "=============================================="
echo ""
echo "Resource group:  $RESOURCE_GROUP"
echo "API (Web App):   https://$API_APP_NAME.azurewebsites.net"
echo "Web (Static):    https://$STATIC_WEB_APP_NAME.azurestaticapps.net"
echo ""
echo "Next: deploy code (API + frontend) with:"
echo "  export RESOURCE_GROUP=$RESOURCE_GROUP"
echo "  export API_APP_NAME=$API_APP_NAME"
echo "  export STATIC_WEB_APP_NAME=$STATIC_WEB_APP_NAME"
echo "  ./scripts/azure/deploy-fresh-v3.sh"
echo ""
echo "Or run deploy-fresh-v3.sh; it uses these v3 names by default."
echo ""
