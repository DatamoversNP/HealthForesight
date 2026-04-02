#!/usr/bin/env bash
# =============================================================================
# HealthForesight — Azure: one entry point for deploy / DB fix / verify
#
# ISSUES WE FIXED (code + infra patterns)
# ---------------------------------------
# 1) Placeholder DATABASE_URL (USER:PASS@HOST...) on App Service
#    → breaks API/DB; Azure cannot recover old password.
#    → fix-db: set-database-url-on-apps.sh resets PG admin password (RBAC) and
#      writes real DATABASE_URL to API + worker.
#
# 2) Timeouts on heavy SQL / claim breakdowns
#    → PG_STATEMENT_TIMEOUT_MS (default 180s) + SET LOCAL on heavy routes.
#
# 3) Elasticity / daily jobs timing out when Celery unavailable
#    → POST returns fast; BackgroundTasks fallback; worker runs Celery when
#      REDIS_URL + worker app are correct.
#
# 4) Production needs API + Redis + Celery worker (not API-only)
#    → deploy-full / deploy-stack build worker image, set REDIS_URL on both apps.
#
# 5) Gunicorn killing long work
#    → API docker-entrypoint uses --timeout 600; worker has health HTTP on PORT.
#
# 6) zsh: "command not found: #"
#    → Do not paste comment lines (# ...) as commands; only run real commands.
#
# 7) deploy-production-stack refusing template REDIS/DB URLs
#    → Use deploy-full (auto) or fix-db first, then deploy-stack with real URLs.
#
# 8) No Azure Cache for Redis in the resource group
#    → PROVISION_REDIS=1 (creates Basic C0) or paste REDIS_URL before deploy-full.
#
# SECRETS
# -------
# - Do not commit passwords. Use a password manager.
# - production.azure.env is gitignored for manual env if you avoid auto script.
#
# =============================================================================
# USAGE (run from repo root)
# =============================================================================
#   ./scripts/azure/healthforesight-azure-master.sh help
#
#   # After placeholder DATABASE_URL — set new PG password + fix both Web Apps:
#   export NEW_POSTGRES_PASSWORD='YourStrongPassword!'
#   ./scripts/azure/healthforesight-azure-master.sh fix-db
#
#   # Full production: az discovers PG+Redis, you supply PG password; then stack:
#   export POSTGRES_PASSWORD='...'    # current admin password (after fix-db)
#   ./scripts/azure/healthforesight-azure-master.sh deploy-full
#
#   # Stack only (you already have DATABASE_URL + REDIS_URL in env or file):
#   PRODUCTION_ENV_FILE=scripts/azure/production.azure.env ./scripts/azure/healthforesight-azure-master.sh deploy-stack
#
#   # Quick check: DATABASE_URL not template + API ping:
#   ./scripts/azure/healthforesight-azure-master.sh verify
#
#   # Rebuild API container only (ACR + Web App), no worker/redis/db steps:
#   ./scripts/azure/healthforesight-azure-master.sh api-image
#
# Defaults: RESOURCE_GROUP=healthforesight-rg  API_APP_NAME=healthforesight-api
#           WORKER_APP_NAME=healthforesight-worker
# =============================================================================

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

usage() {
  cat <<'USAGE'
HealthForesight Azure — commands (defaults: RG=healthforesight-rg, API=healthforesight-api)

  help              Show this help
  fix-db            Reset PG admin password + set DATABASE_URL on API + worker
                    Need: NEW_POSTGRES_PASSWORD='...'  (or SKIP_PASSWORD_RESET + POSTGRES_PASSWORD)
  deploy-full       az discovers PG + Redis; need POSTGRES_PASSWORD; runs full stack
                    If no Redis in RG: PROVISION_REDIS=1 or export REDIS_URL='rediss://...'
  deploy-stack      Uses DATABASE_URL + REDIS_URL from env or PRODUCTION_ENV_FILE
  verify            Check DATABASE_URL/REDIS_URL not templates; curl API ping
  api-image         Rebuild/push API container only (deploy-api-docker.sh)

Examples (repo root):
  ./scripts/azure/healthforesight-azure-master.sh verify

  export NEW_POSTGRES_PASSWORD='...'
  ./scripts/azure/healthforesight-azure-master.sh fix-db

  export POSTGRES_PASSWORD='...'
  ./scripts/azure/healthforesight-azure-master.sh deploy-full

  No Redis in RG — use one line per command (do not put # comments after a line; zsh runs # and stray words as commands):
  export POSTGRES_PASSWORD='...'
  export REDIS_NEW_NAME=mycompany-hf-redis01
  export PROVISION_REDIS=1
  ./scripts/azure/healthforesight-azure-master.sh deploy-full
  (REDIS_NEW_NAME and PROVISION_REDIS must be exported — a plain assignment is not visible to the script.)

See script header in healthforesight-azure-master.sh for full issue list and notes.
USAGE
}

cmd="${1:-help}"
if [[ "$cmd" == "help" || "$cmd" == "-h" || "$cmd" == "--help" ]]; then
  usage
  exit 0
fi

shift || true

case "$cmd" in
  fix-db)
    exec "$SCRIPT_DIR/set-database-url-on-apps.sh" "$@"
    ;;
  deploy-full|full)
    exec "$SCRIPT_DIR/deploy-production-azure-auto.sh" "$@"
    ;;
  deploy-stack|stack)
    exec "$SCRIPT_DIR/deploy-production-stack.sh" "$@"
    ;;
  api-image|api-docker)
    exec "$SCRIPT_DIR/deploy-api-docker.sh" "$@"
    ;;
  verify|check)
    RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
    API_APP_NAME="${API_APP_NAME:-healthforesight-api}"
    WORKER_APP_NAME="${WORKER_APP_NAME:-healthforesight-worker}"

    if ! az account show &>/dev/null; then
      echo "ERROR: az login required for verify."
      exit 1
    fi

    echo "--- DATABASE_URL (API) ---"
    DBURL=$(az webapp config appsettings list --resource-group "$RESOURCE_GROUP" --name "$API_APP_NAME" \
      --query "[?name=='DATABASE_URL'].value" -o tsv 2>/dev/null | head -1 || echo "")
    if [[ -z "$DBURL" ]]; then
      echo "MISSING: set with fix-db or deploy-full / deploy-stack."
    elif [[ "$DBURL" == *"USER:PASS@"* ]] || [[ "$DBURL" == *"HOST.postgres.database.azure.com"* ]]; then
      echo "BAD: still example template. Run:  ./scripts/azure/healthforesight-azure-master.sh fix-db"
    else
      echo "OK: not the example template (host looks real)."
    fi

    echo ""
    echo "--- REDIS_URL (API) ---"
    RURL=$(az webapp config appsettings list --resource-group "$RESOURCE_GROUP" --name "$API_APP_NAME" \
      --query "[?name=='REDIS_URL'].value" -o tsv 2>/dev/null | head -1 || echo "")
    if [[ -z "$RURL" ]]; then
      echo "MISSING: Celery enqueue will fail; run deploy-full or deploy-stack with Redis."
    elif [[ "$RURL" == *"REDIS_ACCESS_KEY"* ]] || [[ "$RURL" == *"YOURNAME.redis.cache.windows.net"* ]]; then
      echo "BAD: example template. Set real Azure Cache for Redis connection string."
    else
      echo "OK: not the example template."
    fi

    echo ""
    echo "--- API ping ---"
    API_URL="https://${API_APP_NAME}.azurewebsites.net"
    code=$(curl -s -o /tmp/hf_ping_body.txt -w "%{http_code}" "${API_URL}/api/v1/ping" || echo "000")
    echo "HTTP $code  ${API_URL}/api/v1/ping"
    if [[ -f /tmp/hf_ping_body.txt ]]; then
      head -c 200 /tmp/hf_ping_body.txt
      echo ""
    fi

    if az webapp show --resource-group "$RESOURCE_GROUP" --name "$WORKER_APP_NAME" &>/dev/null; then
      echo ""
      echo "--- Worker app exists: $WORKER_APP_NAME (check logs for Celery ready) ---"
      echo "  az webapp log tail -g $RESOURCE_GROUP -n $WORKER_APP_NAME"
    fi
    ;;
  *)
    echo "Unknown command: $cmd"
    usage
    exit 1
    ;;
esac
