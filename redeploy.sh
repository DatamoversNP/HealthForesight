#!/usr/bin/env bash
# HealthForesight — redeploy API (container) + Web (App Service) to Azure.
# Run from anywhere; resolves paths from this script’s directory.
#
# Usage (from repo root):
#   chmod +x redeploy.sh   # once
#   ./redeploy.sh
#   ./redeploy.sh --api-only
#   ./redeploy.sh --web-only
#   SKIP_VERIFY=1 ./redeploy.sh
#
# Requires: az login, Docker (for API), Node/npm + zip (for web).
# Env overrides: RESOURCE_GROUP, API_APP_NAME, WEB_APP_NAME, ACR_NAME, API_BACKEND
#
# Static Web Apps (not App Service): use ./scripts/azure/deploy-frontend.sh instead.

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$ROOT/scripts/azure/redeploy-all.sh" "$@"
