#!/usr/bin/env bash
# =============================================================================
# Redeploy HealthForesight to Azure from your laptop (one command).
#
# Run from anywhere:
#   bash /path/to/uepi-migration/scripts/azure/redeploy-azure.sh
# Or from repo root (make executable once: chmod +x scripts/azure/redeploy-azure.sh):
#   ./scripts/azure/redeploy-azure.sh
#
# Options:
#   --api-only          Deploy API container only (passed to redeploy-all.sh)
#   --web-only          Deploy App Service web only (passed to redeploy-all.sh)
#   --refresh-baselines After deploy, POST /api/v1/baselines/refresh-all (needs API_JWT)
#   --refresh-only      Only refresh baselines; no deploy (needs API_JWT)
#   --help              Show this help
#
# Optional — after API is up, refresh all baselines (needs a logged-in JWT):
#   API_JWT='eyJ...' ./scripts/azure/redeploy-azure.sh --api-only --refresh-baselines
#
# Refresh only (no build/deploy; API must already be running):
#   API_JWT='eyJ...' ./scripts/azure/redeploy-azure.sh --refresh-only
#
# Environment overrides (optional):
#   RESOURCE_GROUP   default: healthforesight-rg
#   API_APP_NAME     default: healthforesight-api
#   WEB_APP_NAME     default: healthforesight-web
#   ACR_NAME         default: healthforesightacr
#   API_BASE_URL     default: https://${API_APP_NAME}.azurewebsites.net
#   SKIP_VERIFY=1    Skip post-deploy curl checks
#
# Prerequisites:
#   az login
#   Full deploy: Node.js + npm + zip (for web)
#   API deploy: uses deploy-api-docker.sh (builds in Azure ACR; no local Docker)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

DO_REFRESH_BASELINES=false
REFRESH_ONLY=false
FORWARD_ARGS=()
for arg in "$@"; do
  case "$arg" in
    --refresh-baselines)
      DO_REFRESH_BASELINES=true
      ;;
    --refresh-only)
      REFRESH_ONLY=true
      DO_REFRESH_BASELINES=true
      ;;
    -h|--help)
      sed -n '2,33p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      FORWARD_ARGS+=("$arg")
      ;;
  esac
done

cd "$REPO_ROOT"

export RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
export API_APP_NAME="${API_APP_NAME:-healthforesight-api}"
export WEB_APP_NAME="${WEB_APP_NAME:-healthforesight-web}"
API_BASE_URL="${API_BASE_URL:-https://${API_APP_NAME}.azurewebsites.net}"

echo "=============================================="
echo "redeploy-azure.sh"
echo "REPO_ROOT:       $REPO_ROOT"
echo "Resource group:  $RESOURCE_GROUP"
echo "=============================================="

if [[ "$REFRESH_ONLY" == true ]]; then
  echo "Skipping deploy (--refresh-only)."
else
  # macOS Bash + set -u: "${FORWARD_ARGS[@]}" errors when the array is empty
  if [[ ${#FORWARD_ARGS[@]} -eq 0 ]]; then
    bash "$SCRIPT_DIR/redeploy-all.sh"
  else
    bash "$SCRIPT_DIR/redeploy-all.sh" "${FORWARD_ARGS[@]}"
  fi
fi

if [[ "$DO_REFRESH_BASELINES" != true ]]; then
  echo ""
  echo "Tip: After baseline math fixes, refresh DB baselines on Azure:"
  echo "  1. Log in to the app, copy Bearer token from browser devtools (or API login response)."
  echo "  2. Run:"
  echo "     API_JWT='...your_jwt...' $0 --api-only --refresh-baselines"
  echo "  (Or use Admin / Baseline UI: refresh all baselines.)"
  exit 0
fi

if [[ -z "${API_JWT:-}" ]]; then
  echo ""
  echo "❌ Baseline refresh requires API_JWT (Bearer token from a logged-in user)."
  echo "   Examples:"
  echo "   API_JWT='eyJhbG...' $0 --api-only --refresh-baselines"
  echo "   API_JWT='eyJhbG...' $0 --refresh-only"
  exit 1
fi

echo ""
echo ">>> POST $API_BASE_URL/api/v1/baselines/refresh-all ..."
code=$(curl -sS -o /tmp/hf-refresh-all.json -w '%{http_code}' \
  -X POST \
  -H "Authorization: Bearer $API_JWT" \
  -H "Content-Type: application/json" \
  --max-time 600 \
  "${API_BASE_URL}/api/v1/baselines/refresh-all?baseline_type=ROLLING&window_months=12" \
  || echo "000")

if [[ "$code" != "200" ]]; then
  echo "❌ refresh-all returned HTTP $code"
  head -c 2000 /tmp/hf-refresh-all.json 2>/dev/null || true
  echo ""
  exit 1
fi

echo "✅ Baseline refresh-all completed (HTTP 200). Response (first 800 chars):"
head -c 800 /tmp/hf-refresh-all.json
echo ""
echo ""
echo "Optional: regenerate predicted impacts from the app or your batch script if needed."
exit 0
