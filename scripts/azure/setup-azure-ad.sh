#!/bin/bash
# Script to set up Azure AD for UEPI OIDC authentication

set -e

echo "Azure AD Setup for UEPI"
echo "======================"

# Check Azure CLI
command -v az >/dev/null 2>&1 || { echo "Azure CLI not found. Please install it." >&2; exit 1; }

# Check login
az account show >/dev/null 2>&1 || { 
    echo "Not logged in to Azure. Please login..."
    az login
}

# Get tenant ID
TENANT_ID=$(az account show --query tenantId -o tsv)
echo "Tenant ID: ${TENANT_ID}"

# Create App Registration for API
echo ""
echo "Creating App Registration for API..."
API_APP_ID=$(az ad app create \
    --display-name "UEPI API" \
    --web-redirect-uris "https://api.uepi.yourdomain.com/api/v1/auth/callback" \
    --query appId -o tsv)

echo "API App ID: ${API_APP_ID}"

# Create App Registration for Web
echo ""
echo "Creating App Registration for Web..."
WEB_APP_ID=$(az ad app create \
    --display-name "UEPI Web" \
    --web-redirect-uris "https://uepi.yourdomain.com/auth/callback" \
    --query appId -o tsv)

echo "Web App ID: ${WEB_APP_ID}"

# Create Service Principal for API
echo ""
echo "Creating Service Principal for API..."
az ad sp create --id "${API_APP_ID}"

# Create Service Principal for Web
echo ""
echo "Creating Service Principal for Web..."
az ad sp create --id "${WEB_APP_ID}"

# Get OIDC endpoints
OIDC_ISSUER="https://login.microsoftonline.com/${TENANT_ID}/v2.0"
OIDC_JWKS_URI="${OIDC_ISSUER}/.well-known/openid-configuration"

echo ""
echo "OIDC Configuration:"
echo "==================="
echo "Issuer: ${OIDC_ISSUER}"
echo "JWKS URI: ${OIDC_JWKS_URI}"
echo "API App ID: ${API_APP_ID}"
echo "Web App ID: ${WEB_APP_ID}"
echo ""
echo "Next steps:"
echo "1. Configure API permissions in Azure Portal"
echo "2. Add client secret for API app"
echo "3. Update Helm values with OIDC_ISSUER"
echo "4. Update web app with API App ID as audience"

