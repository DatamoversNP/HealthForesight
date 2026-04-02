#!/bin/bash
# Deploy Frontend to Azure Static Web Apps

set -e

# Configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
STATIC_WEB_APP_NAME="${STATIC_WEB_APP_NAME:-healthforesight-web}"
API_URL="${API_URL:-https://healthforesight-api.azurewebsites.net}"
# Optional: VITE_AUTH_STORAGE=session — JWT in sessionStorage only (new browser session → login page).
# Leave unset to keep default localStorage (stay signed in until logout or token expiry).

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
if [ -n "${VITE_AUTH_STORAGE:-}" ]; then
  echo "VITE_AUTH_STORAGE=$VITE_AUTH_STORAGE" >> .env.production
  echo "✅ Set VITE_AUTH_STORAGE=$VITE_AUTH_STORAGE"
fi

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

echo "Getting deployment token (for Static Web App)..."
DEPLOYMENT_TOKEN=$(az staticwebapp secrets list \
  --name $STATIC_WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "properties.apiKey" \
  --output tsv 2>/dev/null || echo "")

if [ -n "$DEPLOYMENT_TOKEN" ]; then
  echo "Deploying to Azure Static Web Apps..."
  swa deploy ./dist \
    --deployment-token "$DEPLOYMENT_TOKEN" \
    --env production
  echo ""
  echo "✅ Deployment completed!"
  echo "Frontend URL: https://$STATIC_WEB_APP_NAME.azurestaticapps.net"
else
  # App Service Web App: Node + server.mjs proxies /api → backend (no browser CORS)
  if az webapp show --resource-group "$RESOURCE_GROUP" --name "$STATIC_WEB_APP_NAME" --output none 2>/dev/null; then
    echo "Static Web App not found; deploying Node proxy + SPA to '$STATIC_WEB_APP_NAME'..."
    if [[ "$API_URL" == *"/api/v1"* ]]; then
      VITE_API_URL_VALUE="$API_URL"
    else
      VITE_API_URL_VALUE="$API_URL/api/v1"
    fi
    echo "VITE_API_URL=$VITE_API_URL_VALUE" > .env.production
    if [ -n "${VITE_AUTH_STORAGE:-}" ]; then
      echo "VITE_AUTH_STORAGE=$VITE_AUTH_STORAGE" >> .env.production
      echo "✅ VITE_AUTH_STORAGE=$VITE_AUTH_STORAGE"
    fi
    echo "Building with VITE_API_URL=$VITE_API_URL_VALUE (direct API; proxy still serves /api if used)..."
    npm run build:skip-check
    if [ -f "staticwebapp.config.json" ]; then
      cp staticwebapp.config.json dist/staticwebapp.config.json 2>/dev/null || true
    fi
    echo "Production node_modules for server..."
    rm -rf node_modules
    npm install --omit=dev --no-audit --no-fund
    WEB_DEPLOY_ZIP="${TMPDIR:-/tmp}/web-deploy-$(date +%s)-$$.zip"
    rm -f "$WEB_DEPLOY_ZIP"
    zip -r -q "$WEB_DEPLOY_ZIP" package.json package-lock.json server.mjs dist node_modules
    API_BACKEND="${API_URL%/}"
    API_BACKEND="${API_BACKEND%/api/v1}"
    az webapp config appsettings set \
      --resource-group "$RESOURCE_GROUP" \
      --name "$STATIC_WEB_APP_NAME" \
      --settings "API_BACKEND_URL=$API_BACKEND" "WEBSITE_NODE_DEFAULT_VERSION=~20" \
      --output none 2>/dev/null || true
    az webapp config set \
      --resource-group "$RESOURCE_GROUP" \
      --name "$STATIC_WEB_APP_NAME" \
      --linux-fx-version "NODE|20-lts" \
      --output none 2>/dev/null || true
    az webapp config set \
      --resource-group "$RESOURCE_GROUP" \
      --name "$STATIC_WEB_APP_NAME" \
      --startup-command "node server.mjs" \
      --output none 2>/dev/null || echo "⚠️  Portal → Configuration → General → Stack Node 20, Startup: node server.mjs"
    az webapp deploy \
      --resource-group "$RESOURCE_GROUP" \
      --name "$STATIC_WEB_APP_NAME" \
      --src-path "$WEB_DEPLOY_ZIP" \
      --type zip
    rm -f "$WEB_DEPLOY_ZIP"
    echo ""
    echo "✅ Deployment completed!"
    echo "Frontend: https://$STATIC_WEB_APP_NAME.azurewebsites.net  (API proxy → $API_BACKEND)"
  else
    echo "⚠️  Could not get Static Web App deployment token, and Web App '$STATIC_WEB_APP_NAME' not found."
    echo ""
    echo "Build output is in: ./dist"
    echo "To deploy manually: create a Static Web App or Web App, or get the deployment token from Azure Portal."
    exit 1
  fi
fi

