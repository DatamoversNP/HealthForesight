#!/usr/bin/env bash
# =============================================================================
# HealthForesight – full Azure redeploy (API container + Web App Node/SPA)
#
# From repo root:
#   ./scripts/azure/redeploy-all.sh
#   ./scripts/azure/redeploy-all.sh --api-only
#   ./scripts/azure/redeploy-all.sh --web-only
#   SKIP_VERIFY=1 ./scripts/azure/redeploy-all.sh    # skip post-deploy HTTP checks
#
# Prerequisites:
#   - az login (subscription with the resource group)
#   - Node.js + npm, zip (for web)
#   - API Web App configured for Linux container; ACR access (script creates Basic ACR if missing)
#
# Environment (optional overrides):
#   RESOURCE_GROUP   default: healthforesight-rg
#   API_APP_NAME     default: healthforesight-api
#   WEB_APP_NAME     default: healthforesight-web
#   ACR_NAME         default: healthforesightacr
#   API_BACKEND      default: https://${API_APP_NAME}.azurewebsites.net
#   VITE_AUTH_STORAGE  optional: session → JWT in sessionStorage only
#   SKIP_VERIFY      set to 1 to skip curl health checks (not recommended)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

export RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
export API_APP_NAME="${API_APP_NAME:-healthforesight-api}"
export WEB_APP_NAME="${WEB_APP_NAME:-healthforesight-web}"
export ACR_NAME="${ACR_NAME:-healthforesightacr}"
export API_BACKEND="${API_BACKEND:-https://${API_APP_NAME}.azurewebsites.net}"

DO_API=true
DO_WEB=true
for arg in "$@"; do
  case "$arg" in
    --api-only) DO_WEB=false ;;
    --web-only) DO_API=false ;;
    -h|--help)
      sed -n '2,24p' "$0" | sed 's/^# \{0,1\}//'
      echo ""
      echo "Static Web Apps (not App Service): use ./scripts/azure/deploy-frontend.sh"
      exit 0
      ;;
  esac
done

wait_for_http() {
  local url=$1
  local label=$2
  local max_attempts=${3:-36}
  local sleep_sec=${4:-10}
  local i=1
  local code
  while [[ $i -le $max_attempts ]]; do
    code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 30 "$url" 2>/dev/null || echo "000")
    if [[ "$code" == "200" ]]; then
      echo "✅ $label (HTTP 200)"
      return 0
    fi
    echo "   [$i/$max_attempts] $label → HTTP ${code:-000} (retry in ${sleep_sec}s)"
    sleep "$sleep_sec"
    i=$((i + 1))
  done
  echo "❌ $label — no HTTP 200 after $max_attempts attempts (~$((max_attempts * sleep_sec))s)"
  return 1
}

echo "=============================================="
echo "HealthForesight – Redeploy (API + Web)"
echo "=============================================="
echo "REPO_ROOT:      $REPO_ROOT"
echo "Resource group: $RESOURCE_GROUP"
echo "API app:        $API_APP_NAME"
echo "Web app:        $WEB_APP_NAME"
echo "API backend:    $API_BACKEND"
echo "Deploy API:     $DO_API  |  Deploy Web: $DO_WEB"
echo "=============================================="

if ! command -v az &>/dev/null; then
  echo "❌ Azure CLI (az) not found. https://aka.ms/InstallAzureCLI"
  exit 1
fi
if ! az account show &>/dev/null; then
  echo "❌ Not logged in. Run: az login"
  exit 1
fi

if [[ "$DO_API" == true ]]; then
  if ! az webapp show --resource-group "$RESOURCE_GROUP" --name "$API_APP_NAME" &>/dev/null; then
    echo "❌ API Web App not found: $API_APP_NAME in $RESOURCE_GROUP"
    exit 1
  fi
fi

if [[ "$DO_WEB" == true ]]; then
  if ! command -v npm &>/dev/null; then
    echo "❌ npm not found. Install Node.js LTS."
    exit 1
  fi
  if ! command -v zip &>/dev/null; then
    echo "❌ zip not found."
    exit 1
  fi
  if ! az webapp show --resource-group "$RESOURCE_GROUP" --name "$WEB_APP_NAME" &>/dev/null; then
    echo "❌ Web App not found: $WEB_APP_NAME in $RESOURCE_GROUP"
    exit 1
  fi
fi

if [[ "$DO_API" == true ]]; then
  echo ""
  echo ">>> [1/2] API — Docker build (ACR) + configure App Service ..."
  bash "$SCRIPT_DIR/deploy-api-docker.sh"
fi

if [[ "$DO_WEB" == true ]]; then
  echo ""
  echo ">>> [2/2] Web — build SPA + Node server + zip deploy ..."
  export WEB_APP_NAME
  bash "$SCRIPT_DIR/deploy-web-appservice-full.sh"
fi

API_PUBLIC="https://${API_APP_NAME}.azurewebsites.net"
WEB_PUBLIC="https://${WEB_APP_NAME}.azurewebsites.net"

echo ""
echo "=============================================="
echo "Deploy steps finished"
echo "=============================================="
echo "API:  $API_PUBLIC"
echo "Web:  $WEB_PUBLIC"
echo "=============================================="

if [[ "${SKIP_VERIFY:-0}" == "1" ]]; then
  echo "SKIP_VERIFY=1 — skipping HTTP checks. Test manually:"
  echo "  curl -sS \"$API_PUBLIC/api/v1/ping\""
  exit 0
fi

VERIFY_FAILED=0

if [[ "$DO_API" == true ]]; then
  echo ""
  echo ">>> Verifying API (container can take 1–6 minutes after restart) ..."
  if ! wait_for_http "$API_PUBLIC/api/v1/ping" "API GET /api/v1/ping" 36 10; then
    VERIFY_FAILED=1
  else
    curl -sS "$API_PUBLIC/api/v1/ping" | head -c 200 || true
    echo ""
  fi
fi

if [[ "$DO_WEB" == true ]]; then
  echo ""
  echo ">>> Verifying Web App (Node may need ~1–2 minutes) ..."
  if ! wait_for_http "$WEB_PUBLIC/" "Web GET /" 24 10; then
    VERIFY_FAILED=1
  fi
  echo ">>> Verifying Web → API proxy (optional) ..."
  proxy_code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 30 "$WEB_PUBLIC/api/v1/ping" 2>/dev/null || echo "000")
  if [[ "$proxy_code" == "200" ]]; then
    echo "✅ Web proxy GET /api/v1/ping (HTTP 200)"
  else
    echo "⚠️  Web proxy GET /api/v1/ping → HTTP $proxy_code (SPA may still work via baked VITE_API_URL)"
  fi
fi

if [[ "$VERIFY_FAILED" -ne 0 ]]; then
  echo ""
  echo "❌ Post-deploy verification failed. Check:"
  echo "   - API: Portal → $API_APP_NAME → Log stream"
  echo "   - Web: Portal → $WEB_APP_NAME → Log stream; Startup command = node server.mjs"
  exit 1
fi

echo ""
echo "✅ Redeploy complete and verified."
echo "   Open: $WEB_PUBLIC"
exit 0
