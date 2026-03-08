#!/bin/bash
# Deploy Frontend to Azure Static Web Apps

set -e

# Configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
STATIC_WEB_APP_NAME="${STATIC_WEB_APP_NAME:-healthforesight-web-9016}"
API_URL="${API_URL:-https://healthforesight-api-9016.azurewebsites.net}"

echo "Deploying Frontend to Azure Static Web Apps..."

# Load nvm if available
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$HOME/.nvm/nvm.sh" ] && \. "$HOME/.nvm/nvm.sh"

# Use default Node.js version if nvm is available
if command -v nvm &> /dev/null; then
    nvm use default
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found. Please install Node.js and npm, or ensure nvm is loaded."
    echo "   You can install Node.js via:"
    echo "   - nvm: nvm install --lts && nvm use --lts"
    echo "   - Homebrew: brew install node"
    exit 1
fi

# Navigate to web directory
cd "$(dirname "$0")/../../apps/web" || exit 1

# Create production environment file
# Ensure API_URL includes /api/v1 if not already present
if [[ "$API_URL" == *"/api/v1"* ]]; then
    VITE_API_URL_VALUE="$API_URL"
else
    VITE_API_URL_VALUE="$API_URL/api/v1"
fi
echo "VITE_API_URL=$VITE_API_URL_VALUE" > .env.production
echo "✅ Set VITE_API_URL=$VITE_API_URL_VALUE"

# Install dependencies
echo "Installing dependencies..."
npm install

# Build for production (skip TypeScript checking for now)
echo "Building for production (skipping TypeScript checks)..."
npm run build:skip-check

# Ensure staticwebapp.config.json is copied to dist (from root, overwriting any from public/)
echo "Ensuring staticwebapp.config.json is in dist with correct schema..."
if [ -f "staticwebapp.config.json" ]; then
    cp staticwebapp.config.json dist/staticwebapp.config.json
    echo "✅ Copied config from root"
elif [ -f "public/staticwebapp.config.json" ]; then
    cp public/staticwebapp.config.json dist/staticwebapp.config.json
    echo "✅ Copied config from public/"
fi

# Fix any 'fallback' to 'rewrite' (macOS sed syntax)
if [ -f "dist/staticwebapp.config.json" ]; then
    if grep -q '"fallback"' dist/staticwebapp.config.json; then
        echo "Fixing 'fallback' to 'rewrite'..."
        sed -i.bak 's/"fallback"/"rewrite"/g' dist/staticwebapp.config.json
        rm -f dist/staticwebapp.config.json.bak
    fi
    echo "✅ Config file ready in dist/"
fi

# Deploy to Static Web Apps using Static Web Apps CLI
echo "Installing Azure Static Web Apps CLI (if not already installed)..."
if ! command -v swa &> /dev/null; then
    npm install -g @azure/static-web-apps-cli
else
    echo "✅ SWA CLI already installed"
fi

echo "Getting deployment token..."
DEPLOYMENT_TOKEN=$(az staticwebapp secrets list \
  --name $STATIC_WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "properties.apiKey" \
  --output tsv 2>/dev/null || echo "")

if [ -z "$DEPLOYMENT_TOKEN" ]; then
    echo "⚠️  Could not get deployment token automatically."
    echo ""
    echo "Please get the deployment token manually:"
    echo "  1. Run: az staticwebapp secrets list --name $STATIC_WEB_APP_NAME --resource-group $RESOURCE_GROUP"
    echo "  2. Copy the 'apiKey' value"
    echo "  3. Then run: swa deploy ./dist --deployment-token <YOUR_TOKEN>"
    echo ""
    echo "Or get it from Azure Portal:"
    echo "  Azure Portal > Static Web Apps > $STATIC_WEB_APP_NAME > Deployment > Manage deployment token"
    echo ""
    echo "Build output is ready in: ./dist"
    exit 1
fi

echo "Deploying to Azure Static Web Apps..."
swa deploy ./dist \
  --deployment-token "$DEPLOYMENT_TOKEN" \
  --env production

echo ""
echo "✅ Deployment completed!"
echo "Frontend URL: https://$STATIC_WEB_APP_NAME.azurestaticapps.net"

