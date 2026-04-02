#!/bin/bash
# Complete deployment script - Deploys both API and Frontend

set -e

# Configuration from migration
RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api}"
STATIC_WEB_APP_NAME="${STATIC_WEB_APP_NAME:-healthforesight-web}"
API_URL="https://$API_APP_NAME.azurewebsites.net"

echo "=========================================="
echo "Complete Deployment to Azure"
echo "=========================================="
echo ""
echo "Resource Group: $RESOURCE_GROUP"
echo "API App: $API_APP_NAME"
echo "Static Web App: $STATIC_WEB_APP_NAME"
echo "API URL: $API_URL"
echo ""

# Deploy API
echo "Step 1: Deploying API..."
cd "$(dirname "$0")/../../apps/api" || exit 1

# Create deployment package
echo "Creating deployment package..."
zip -r ../../api-deployment.zip . \
  -x "*.pyc" \
  -x "__pycache__/*" \
  -x "*.git*" \
  -x "*.env*" \
  -x "*.log" \
  -x "venv/*" \
  -x ".venv/*" \
  -x "node_modules/*" \
  -x "*.zip" \
  -x "data/*" 2>/dev/null || true

# Deploy to Azure (use az webapp deploy; config-zip is deprecated)
echo "Deploying to Azure..."
az webapp deploy \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --src-path ../../api-deployment.zip \
  --type zip

# Clean up
rm -f ../../api-deployment.zip

echo "✅ API deployed successfully!"
echo ""

# Deploy Frontend
echo "Step 2: Deploying Frontend..."
cd ../web || exit 1

# Create production environment file
echo "VITE_API_URL=$API_URL/api/v1" > .env.production
echo "VITE_API_BASE_URL=$API_URL/api/v1" >> .env.production

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Build for production
echo "Building for production..."
npm run build

# Deploy to Static Web Apps
echo "Deploying to Azure Static Web Apps..."
az staticwebapp deploy \
  --name $STATIC_WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --app-location "./" \
  --output-location "dist"

echo "✅ Frontend deployed successfully!"
echo ""

echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "API URL: $API_URL"
echo "API Docs: $API_URL/docs"
echo "Frontend: Check Azure Portal for Static Web App URL"
echo ""
echo "Test API:"
echo "  curl $API_URL/api/v1/health"
echo ""

