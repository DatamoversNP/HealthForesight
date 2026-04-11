#!/usr/bin/env bash
# =============================================================================
# Complete deploy: Frontend → Azure App Service (healthforesight-web)
# Serves SPA + proxies /api → healthforesight-api (same-origin in browser = no CORS)
#
# Prerequisites: az login, Node 18+, npm, zip
#
# Usage (from anywhere):
#   bash /path/to/repo/scripts/azure/deploy-web-appservice-full.sh
#
# Or from repo root:
#   ./scripts/azure/deploy-web-appservice-full.sh
#
# Override defaults:
#   RESOURCE_GROUP=my-rg WEB_APP_NAME=my-web API_BACKEND=https://my-api.azurewebsites.net \
#     ./scripts/azure/deploy-web-appservice-full.sh
# =============================================================================
set -euo pipefail

# --- Absolute paths (script lives in <repo>/scripts/azure/) ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WEB_DIR="$REPO_ROOT/apps/web"

# --- Azure / API ---
RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
WEB_APP_NAME="${WEB_APP_NAME:-healthforesight-web}"
API_BACKEND="${API_BACKEND:-https://healthforesight-api.azurewebsites.net}"
API_BACKEND="${API_BACKEND%/}"

echo "=============================================="
echo "HealthForesight – Web App (Node + API proxy)"
echo "=============================================="
echo "REPO_ROOT:     $REPO_ROOT"
echo "WEB_DIR:       $WEB_DIR"
echo "Resource grp:  $RESOURCE_GROUP"
echo "Web app:       $WEB_APP_NAME"
echo "API backend:   $API_BACKEND"
echo "=============================================="

if [[ ! -d "$WEB_DIR" ]]; then
  echo "❌ WEB_DIR not found: $WEB_DIR"
  exit 1
fi

if ! command -v az &>/dev/null; then
  echo "❌ Azure CLI (az) not found. Install: https://aka.ms/InstallAzureCLI"
  exit 1
fi

if ! command -v npm &>/dev/null; then
  echo "❌ npm not found. Install Node.js LTS."
  exit 1
fi

if ! command -v zip &>/dev/null; then
  echo "❌ zip not found (needed to build deploy package)."
  exit 1
fi

if ! az account show &>/dev/null; then
  echo "❌ Not logged in. Run: az login"
  exit 1
fi

if ! az webapp show --resource-group "$RESOURCE_GROUP" --name "$WEB_APP_NAME" &>/dev/null; then
  echo "❌ Web app not found: $WEB_APP_NAME in $RESOURCE_GROUP"
  echo "   Create it or set WEB_APP_NAME / RESOURCE_GROUP."
  exit 1
fi

# --- Optional: nvm ---
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" || true

cd "$WEB_DIR"
echo ""
echo ">>> Working directory: $(pwd)"

# Bake API base URL into the SPA so the UI works even if /api proxy is misconfigured (CORS is allowed on API).
API_BACKEND_NORM="${API_BACKEND%/}"
if [[ "$API_BACKEND_NORM" == */api/v1 ]]; then
  VITE_API_URL_VALUE="$API_BACKEND_NORM"
else
  VITE_API_URL_VALUE="${API_BACKEND_NORM}/api/v1"
fi
echo "VITE_API_URL=$VITE_API_URL_VALUE" > .env.production
VITE_APP_BUILD_VALUE="${VITE_APP_BUILD:-$(date -u +%Y%m%dT%H%MZ)-$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo local)}"
echo "VITE_APP_BUILD=$VITE_APP_BUILD_VALUE" >> .env.production
echo ">>> VITE_APP_BUILD=$VITE_APP_BUILD_VALUE (sidebar stamp in UI)"
if [[ -n "${VITE_AUTH_STORAGE:-}" ]]; then
  echo "VITE_AUTH_STORAGE=$VITE_AUTH_STORAGE" >> .env.production
  echo ">>> VITE_AUTH_STORAGE=$VITE_AUTH_STORAGE"
fi
echo ">>> .env.production: VITE_API_URL=$VITE_API_URL_VALUE"

echo ""
echo ">>> npm install (full deps for build)..."
npm install --no-audit --no-fund

echo ""
echo ">>> npm run build:skip-check..."
npm run build:skip-check

if [[ -f staticwebapp.config.json ]]; then
  cp staticwebapp.config.json dist/staticwebapp.config.json 2>/dev/null || true
fi

echo ""
echo ">>> Production node_modules for server.mjs (express + proxy)..."
rm -rf node_modules
npm install --omit=dev --no-audit --no-fund

if [[ ! -f server.mjs ]]; then
  echo "❌ Missing $WEB_DIR/server.mjs"
  exit 1
fi

# mktemp creates an empty file; zip -r into that path fails ("structure invalid").
WEB_DEPLOY_ZIP="${TMPDIR:-/tmp}/hf-web-deploy-$(date +%s)-$$.zip"
rm -f "$WEB_DEPLOY_ZIP"
trap 'rm -f "$WEB_DEPLOY_ZIP"' EXIT

echo ""
echo ">>> Creating zip: package.json, server.mjs, dist/, node_modules/"
cd "$WEB_DIR"
if [[ -f package-lock.json ]]; then
  zip -r -q "$WEB_DEPLOY_ZIP" package.json package-lock.json server.mjs dist node_modules
else
  zip -r -q "$WEB_DEPLOY_ZIP" package.json server.mjs dist node_modules
fi

echo ""
echo ">>> Azure: app settings + Node 20 + startup..."
az webapp config appsettings set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$WEB_APP_NAME" \
  --settings \
    "API_BACKEND_URL=$API_BACKEND" \
    "WEBSITE_NODE_DEFAULT_VERSION=~20" \
  --output none

az webapp config set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$WEB_APP_NAME" \
  --linux-fx-version "NODE|20-lts" \
  --output none

# Startup command (CLI flag name varies; set both patterns if needed)
az webapp config set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$WEB_APP_NAME" \
  --startup-command "node server.mjs" \
  --output none 2>/dev/null || true

echo ""
echo ">>> Azure: zip deploy..."
az webapp deploy \
  --resource-group "$RESOURCE_GROUP" \
  --name "$WEB_APP_NAME" \
  --src-path "$WEB_DEPLOY_ZIP" \
  --type zip

echo ""
echo "=============================================="
echo "✅ Done"
echo "=============================================="
WEB_URL="https://${WEB_APP_NAME}.azurewebsites.net"
echo "URL:     $WEB_URL"
echo "Proxy:   $WEB_URL/api/v1/* → ${API_BACKEND}/api/v1/*"
echo ""
echo "VERIFY (wait ~60s after deploy, then):"
echo "  curl -s -o /dev/null -w 'HTTP %{http_code}\\n' \"$WEB_URL/api/v1/health\""
echo "  → Must be 200. If 404, Node is not running — set Startup: node server.mjs"
echo ""
echo "Browser: hard refresh (Cmd+Shift+R) or Incognito — old index-*.js was cached."
echo "Portal:  $WEB_APP_NAME → Configuration → Node 20, Startup: node server.mjs"
echo "         API_BACKEND_URL = $API_BACKEND"
echo "=============================================="
