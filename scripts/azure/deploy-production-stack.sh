#!/usr/bin/env bash
# =============================================================================
# Production-like Azure stack: API (container) + Celery worker (container) +
# app settings for DB, Redis, timeouts, CORS, and optional frontend deploy.
# =============================================================================
#
# Prerequisites:
#   - az login
#   - Azure Container Registry + Linux App Service Plan (created with API Web App)
#   - Azure Database for PostgreSQL + Azure Cache for Redis (create in portal or CLI)
#
# Required environment variables (export or use PRODUCTION_ENV_FILE):
#   DATABASE_URL   — PostgreSQL connection string (sslmode=require)
#   REDIS_URL      — e.g. rediss://:key@name.redis.cache.windows.net:6380/0
#
# Optional:
#   JWT_SECRET, OBJECT_STORAGE_* (see production.azure.env.example)
#   RESOURCE_GROUP, API_APP_NAME, WORKER_APP_NAME, ACR_NAME, IMAGE_TAG
#   SKIP_FRONTEND=1  — do not run deploy-frontend.sh
#   SKIP_WORKER=1    — API + settings only
#   SKIP_MIGRATIONS, SKIP_SEED — passed through to deploy-complete-full logic below
#   PRODUCTION_ENV_FILE — path to env file (sourced with set -a)
#
# Usage (repo root):
#   PRODUCTION_ENV_FILE=scripts/azure/production.azure.env ./scripts/azure/deploy-production-stack.sh
#
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

if [[ -n "${PRODUCTION_ENV_FILE:-}" && -f "$PRODUCTION_ENV_FILE" ]]; then
  echo "Loading $PRODUCTION_ENV_FILE"
  set -a
  # shellcheck source=/dev/null
  source "$PRODUCTION_ENV_FILE"
  set +a
fi

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api}"
WORKER_APP_NAME="${WORKER_APP_NAME:-healthforesight-worker}"
ACR_NAME="${ACR_NAME:-healthforesightacr}"
STATIC_WEB_APP_NAME="${STATIC_WEB_APP_NAME:-healthforesight-web}"
WORKER_IMAGE_NAME="${WORKER_IMAGE_NAME:-healthforesight-worker}"

if [[ -z "${DATABASE_URL:-}" || -z "${REDIS_URL:-}" ]]; then
  echo "ERROR: Set DATABASE_URL and REDIS_URL (or use PRODUCTION_ENV_FILE=scripts/azure/production.azure.env)."
  echo "See scripts/azure/production.azure.env.example"
  exit 1
fi

# Reject unedited template values (avoids pushing bad connection strings and confusing DNS errors).
_placeholder_db=0
[[ "$DATABASE_URL" == *"HOST.postgres.database.azure.com"* ]] && _placeholder_db=1
[[ "$DATABASE_URL" == *"USER:PASS@"* ]] && _placeholder_db=1
[[ "$DATABASE_URL" == *"__REPLACE_"* ]] && _placeholder_db=1
if [[ "$_placeholder_db" -eq 1 ]]; then
  echo "ERROR: DATABASE_URL still matches the example template (e.g. USER:PASS@HOST.postgres...)."
  echo "Edit production.azure.env and set your real Azure PostgreSQL host, user, password, and database name."
  exit 1
fi
_placeholder_redis=0
[[ "$REDIS_URL" == *"REDIS_ACCESS_KEY"* ]] && _placeholder_redis=1
[[ "$REDIS_URL" == *"YOURNAME.redis.cache.windows.net"* ]] && _placeholder_redis=1
[[ "$REDIS_URL" == *"__REPLACE_"* ]] && _placeholder_redis=1
if [[ "$_placeholder_redis" -eq 1 ]]; then
  echo "ERROR: REDIS_URL still matches the example template (REDIS_ACCESS_KEY or YOURNAME.redis...)."
  echo "Edit production.azure.env: Azure Portal → your Cache for Redis → Access keys → connection string (port 6380, rediss://)."
  exit 1
fi
if [[ "${JWT_SECRET:-}" == "change-me-long-random" ]]; then
  echo "WARNING: JWT_SECRET is still the example value; set a long random secret before going live."
fi

if [[ -z "${IMAGE_TAG:-}" ]]; then
  if GIT_SHORT=$(git -C "$PROJECT_ROOT" rev-parse --short HEAD 2>/dev/null); then
    IMAGE_TAG="$GIT_SHORT"
  else
    IMAGE_TAG="latest"
  fi
fi

export RESOURCE_GROUP API_APP_NAME IMAGE_TAG ACR_NAME

API_URL="https://${API_APP_NAME}.azurewebsites.net"
FRONTEND_SWA_URL="https://${STATIC_WEB_APP_NAME}.azurestaticapps.net"
FRONTEND_WEBAPP_URL="https://${STATIC_WEB_APP_NAME}.azurewebsites.net"
CORS_ORIGINS="${CORS_ORIGINS:-$FRONTEND_SWA_URL,$FRONTEND_WEBAPP_URL,http://localhost:3050,http://localhost:3000}"

echo "=============================================="
echo "HealthForesight — production stack deploy"
echo "=============================================="
echo "Resource group:  $RESOURCE_GROUP"
echo "API:             $API_APP_NAME"
echo "Worker:          $WORKER_APP_NAME"
echo "ACR:             $ACR_NAME"
echo "Image tag:       $IMAGE_TAG"
echo ""

# --- API: build & deploy container (reuse ACR build flow) ---
echo "--- Step 1: API container (ACR build + Web App) ---"
"$SCRIPT_DIR/deploy-api-docker.sh"

ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query loginServer -o tsv)
FULL_WORKER_IMAGE="${ACR_LOGIN_SERVER}/${WORKER_IMAGE_NAME}:${IMAGE_TAG}"

echo "--- Step 2: API app settings (DB, Redis, timeouts, CORS, JWT) ---"
SETTINGS_ARGS=(
  "DATABASE_URL=$DATABASE_URL"
  "REDIS_URL=$REDIS_URL"
  "PG_STATEMENT_TIMEOUT_MS=${PG_STATEMENT_TIMEOUT_MS:-180000}"
  "CORS_ORIGINS=$CORS_ORIGINS"
  "WEBSITES_PORT=8080"
  "PORT=8080"
  "PYTHONPATH=/app/apps/api/src:/app/packages/common/src"
)
if [[ -n "${JWT_SECRET:-}" ]]; then
  SETTINGS_ARGS+=("JWT_SECRET=$JWT_SECRET")
fi
# Object storage (optional; forward common vars if set)
for v in OBJECT_STORAGE_ENDPOINT OBJECT_STORAGE_ACCESS_KEY OBJECT_STORAGE_SECRET_KEY OBJECT_STORAGE_BUCKET; do
  if [[ -n "${!v:-}" ]]; then
    SETTINGS_ARGS+=("$v=${!v}")
  fi
done

az webapp config appsettings set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$API_APP_NAME" \
  --settings "${SETTINGS_ARGS[@]}" \
  --output none

az webapp restart --resource-group "$RESOURCE_GROUP" --name "$API_APP_NAME" --output none
echo "API app settings applied and restarted."

# --- Worker image ---
if [[ -z "${SKIP_WORKER:-}" ]]; then
  echo "--- Step 3: Build worker image in ACR ---"
  az acr build --registry "$ACR_NAME" \
    --image "${WORKER_IMAGE_NAME}:${IMAGE_TAG}" \
    --image "${WORKER_IMAGE_NAME}:latest" \
    --file apps/worker/Dockerfile \
    "$PROJECT_ROOT"

  az acr update --name "$ACR_NAME" --admin-enabled true --output none 2>/dev/null || true
  ACR_USER=$(az acr credential show --name "$ACR_NAME" --query username -o tsv)
  ACR_PASS=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)

  PLAN_ID=$(az webapp show --resource-group "$RESOURCE_GROUP" --name "$API_APP_NAME" --query appServicePlanId -o tsv)
  PLAN_NAME=$(basename "$PLAN_ID")

  if ! az webapp show --resource-group "$RESOURCE_GROUP" --name "$WORKER_APP_NAME" &>/dev/null; then
    echo "Creating Web App $WORKER_APP_NAME (Linux container) on plan $PLAN_NAME ..."
    az webapp create \
      --resource-group "$RESOURCE_GROUP" \
      --plan "$PLAN_NAME" \
      --name "$WORKER_APP_NAME" \
      --deployment-container-image-name "$FULL_WORKER_IMAGE" \
      --output none
  else
    echo "Worker Web App $WORKER_APP_NAME already exists; updating image and registry..."
  fi

  az webapp config container set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$WORKER_APP_NAME" \
    --docker-custom-image-name "$FULL_WORKER_IMAGE" \
    --docker-registry-server-url "https://${ACR_LOGIN_SERVER}" \
    --docker-registry-server-user "$ACR_USER" \
    --docker-registry-server-password "$ACR_PASS" \
    --output none

  echo "--- Step 4: Worker app settings ---"
  WORKER_SETTINGS=(
    "DATABASE_URL=$DATABASE_URL"
    "REDIS_URL=$REDIS_URL"
    "WEBSITES_PORT=8080"
    "PORT=8080"
    "PYTHONPATH=/app/src:/app/apps/api/src:/app/packages/common/src"
    "PG_STATEMENT_TIMEOUT_MS=${PG_STATEMENT_TIMEOUT_MS:-180000}"
  )
  for v in OBJECT_STORAGE_ENDPOINT OBJECT_STORAGE_ACCESS_KEY OBJECT_STORAGE_SECRET_KEY OBJECT_STORAGE_BUCKET; do
    if [[ -n "${!v:-}" ]]; then
      WORKER_SETTINGS+=("$v=${!v}")
    fi
  done

  az webapp config appsettings set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$WORKER_APP_NAME" \
    --settings "${WORKER_SETTINGS[@]}" \
    --output none

  az webapp config set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$WORKER_APP_NAME" \
    --startup-command "" \
    --output none 2>/dev/null || true

  # Always On helps the worker stay running (consumption may still sleep on free tier).
  az webapp config set --resource-group "$RESOURCE_GROUP" --name "$WORKER_APP_NAME" --always-on true --output none 2>/dev/null || true

  az webapp restart --resource-group "$RESOURCE_GROUP" --name "$WORKER_APP_NAME" --output none
  echo "Worker deployed: https://${WORKER_APP_NAME}.azurewebsites.net (health check only; API remains $API_URL)"
else
  echo "--- Step 3–4: SKIP_WORKER set — Celery not deployed ---"
fi

# --- Frontend ---
if [[ -z "${SKIP_FRONTEND:-}" ]]; then
  echo "--- Step 5: Frontend (Static Web Apps) ---"
  export API_URL
  "$SCRIPT_DIR/deploy-frontend.sh" || echo "Warning: frontend deploy failed (check SWA resource / token)."
else
  echo "--- Step 5: SKIP_FRONTEND set ---"
fi

# --- DB migrations & seed (optional) ---
export API_URL
if [[ -z "${SKIP_MIGRATIONS:-}" && -n "${DATABASE_URL}" ]]; then
  echo "--- Step 6: Alembic migrations ---"
  cd "$PROJECT_ROOT/apps/api" || exit 1
  export PYTHONPATH="${PROJECT_ROOT}/apps/api/src:${PROJECT_ROOT}/packages/common/src"
  python3 -m alembic upgrade head && echo "Migrations OK." || echo "Warning: migrations failed — run manually with DATABASE_URL set."
  cd "$PROJECT_ROOT" || exit 1
fi

if [[ -z "${SKIP_SEED:-}" && -n "${DATABASE_URL}" ]]; then
  echo "--- Step 7: Seed users (optional script) ---"
  export PYTHONPATH="${PROJECT_ROOT}/apps/api/src:${PROJECT_ROOT}/packages/common/src"
  python3 "$PROJECT_ROOT/scripts/seed_users.py" && echo "Seed OK." || echo "Warning: seed failed or skipped."
fi

echo ""
echo "=============================================="
echo "Production stack deploy finished"
echo "=============================================="
echo "API:       $API_URL"
echo "API ping:  $API_URL/api/v1/ping"
if [[ -z "${SKIP_WORKER:-}" ]]; then
  echo "Worker:    https://${WORKER_APP_NAME}.azurewebsites.net (container; Celery + Azure health port)"
  echo "Verify worker log stream: az webapp log tail -g $RESOURCE_GROUP -n $WORKER_APP_NAME"
fi
echo ""
echo "Elasticity & daily jobs use Celery when REDIS_URL is valid; API falls back to BackgroundTasks if the worker is down."
echo "Tune PG_STATEMENT_TIMEOUT_MS (ms) if you still see DB cancellations on heavy reports."
echo ""
