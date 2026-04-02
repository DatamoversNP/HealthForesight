#!/usr/bin/env bash
# =============================================================================
# Fix placeholder DATABASE_URL on App Service:
#   1) Discover PostgreSQL in the resource group
#   2) Set a NEW admin password on the server (no old password needed — Azure RBAC)
#   3) Build DATABASE_URL and apply to API + worker Web Apps, then restart
#
# Usage (repo root):
#   export NEW_POSTGRES_PASSWORD='YourStrongPassword1!'
#   ./scripts/azure/set-database-url-on-apps.sh
#
# If you already know the current password and only need to fix app settings:
#   export SKIP_PASSWORD_RESET=1
#   export POSTGRES_PASSWORD='current-password'
#   ./scripts/azure/set-database-url-on-apps.sh
#
# Optional: RESOURCE_GROUP, POSTGRES_SERVER_NAME, POSTGRES_DB_NAME (default postgres),
#           API_APP_NAME (default healthforesight-api), WORKER_APP_NAME (default healthforesight-worker)
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api}"
WORKER_APP_NAME="${WORKER_APP_NAME:-healthforesight-worker}"
POSTGRES_DB_NAME="${POSTGRES_DB_NAME:-postgres}"

if ! command -v az &>/dev/null || ! az account show &>/dev/null; then
  echo "ERROR: az login required."
  exit 1
fi
if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 required."
  exit 1
fi

_urlencode() {
  python3 -c 'import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=""))' "$1"
}

PG_FQDN=""
PG_USER=""
PG_KIND=""

resolve_postgres() {
  local name="$1"
  if az postgres flexible-server show --resource-group "$RESOURCE_GROUP" --name "$name" &>/dev/null; then
    PG_FQDN=$(az postgres flexible-server show --resource-group "$RESOURCE_GROUP" --name "$name" --query fullyQualifiedDomainName -o tsv)
    PG_USER=$(az postgres flexible-server show --resource-group "$RESOURCE_GROUP" --name "$name" --query administratorLogin -o tsv)
    PG_KIND="flexible"
    POSTGRES_SERVER_NAME="$name"
    return 0
  fi
  if az postgres server show --resource-group "$RESOURCE_GROUP" --name "$name" &>/dev/null; then
    PG_FQDN=$(az postgres server show --resource-group "$RESOURCE_GROUP" --name "$name" --query fullyQualifiedDomainName -o tsv)
    PG_USER=$(az postgres server show --resource-group "$RESOURCE_GROUP" --name "$name" --query administratorLogin -o tsv)
    PG_KIND="single"
    POSTGRES_SERVER_NAME="$name"
    return 0
  fi
  return 1
}

if [[ -n "${POSTGRES_SERVER_NAME:-}" ]]; then
  resolve_postgres "$POSTGRES_SERVER_NAME" || { echo "ERROR: Server not found."; exit 1; }
else
  NF=$(az postgres flexible-server list --resource-group "$RESOURCE_GROUP" --query "length(@)" -o tsv 2>/dev/null || echo 0)
  if [[ "$NF" =~ ^[0-9]+$ ]] && [[ "$NF" -eq 1 ]]; then
    POSTGRES_SERVER_NAME=$(az postgres flexible-server list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv)
    resolve_postgres "$POSTGRES_SERVER_NAME" || exit 1
  elif [[ "$NF" =~ ^[0-9]+$ ]] && [[ "$NF" -gt 1 ]]; then
    PICK=""
    while IFS= read -r line; do
      [[ -z "$line" ]] && continue
      if echo "$line" | grep -qi postgres || echo "$line" | grep -qi uepi; then PICK="$line"; break; fi
    done < <(az postgres flexible-server list --resource-group "$RESOURCE_GROUP" --query "[].name" -o tsv)
    [[ -z "$PICK" ]] && PICK=$(az postgres flexible-server list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv)
    resolve_postgres "$PICK" || exit 1
  else
    NS=$(az postgres server list --resource-group "$RESOURCE_GROUP" --query "length(@)" -o tsv 2>/dev/null || echo 0)
    if [[ "$NS" =~ ^[0-9]+$ ]] && [[ "$NS" -eq 1 ]]; then
      POSTGRES_SERVER_NAME=$(az postgres server list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv)
      resolve_postgres "$POSTGRES_SERVER_NAME" || exit 1
    else
      echo "ERROR: No PostgreSQL server found in $RESOURCE_GROUP. Set POSTGRES_SERVER_NAME."
      exit 1
    fi
  fi
fi

echo "PostgreSQL: $POSTGRES_SERVER_NAME ($PG_KIND)  FQDN=$PG_FQDN  admin=$PG_USER  db=$POSTGRES_DB_NAME"

USE_PASS=""
if [[ -n "${SKIP_PASSWORD_RESET:-}" ]]; then
  USE_PASS="${POSTGRES_PASSWORD:-}"
  if [[ -z "$USE_PASS" ]]; then
    read -r -s -p "Current PostgreSQL admin password: " USE_PASS
    echo ""
  fi
else
  USE_PASS="${NEW_POSTGRES_PASSWORD:-}"
  if [[ -z "$USE_PASS" ]]; then
    read -r -s -p "NEW PostgreSQL admin password (will be set on server): " USE_PASS
    echo ""
  fi
  echo "Setting admin password on Azure..."
  if [[ "$PG_KIND" == "flexible" ]]; then
    az postgres flexible-server update \
      --resource-group "$RESOURCE_GROUP" \
      --name "$POSTGRES_SERVER_NAME" \
      --admin-password "$USE_PASS" \
      --output none
  else
    az postgres server update \
      --resource-group "$RESOURCE_GROUP" \
      --name "$POSTGRES_SERVER_NAME" \
      --admin-password "$USE_PASS" \
      --output none
  fi
  echo "Server password updated."
fi

if [[ -z "$USE_PASS" ]]; then
  echo "ERROR: Empty password."
  exit 1
fi

ENC_USER=$(_urlencode "$PG_USER")
ENC_PASS=$(_urlencode "$USE_PASS")
DATABASE_URL="postgresql://${ENC_USER}:${ENC_PASS}@${PG_FQDN}:5432/${POSTGRES_DB_NAME}?sslmode=require"

echo "Applying DATABASE_URL to $API_APP_NAME ..."
az webapp config appsettings set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$API_APP_NAME" \
  --settings "DATABASE_URL=$DATABASE_URL" \
  --output none

if az webapp show --resource-group "$RESOURCE_GROUP" --name "$WORKER_APP_NAME" &>/dev/null; then
  echo "Applying DATABASE_URL to $WORKER_APP_NAME ..."
  az webapp config appsettings set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$WORKER_APP_NAME" \
    --settings "DATABASE_URL=$DATABASE_URL" \
    --output none
else
  echo "Worker app $WORKER_APP_NAME not found (skip)."
fi

echo "Restarting web apps..."
az webapp restart --resource-group "$RESOURCE_GROUP" --name "$API_APP_NAME" --output none
if az webapp show --resource-group "$RESOURCE_GROUP" --name "$WORKER_APP_NAME" &>/dev/null; then
  az webapp restart --resource-group "$RESOURCE_GROUP" --name "$WORKER_APP_NAME" --output none
fi

echo ""
echo "Done. Verify:"
echo "  az webapp config appsettings list -g $RESOURCE_GROUP -n $API_APP_NAME --query \"[?name=='DATABASE_URL'].value\" -o tsv | sed 's/:[^:@]*@/:****@/'"
echo "  curl -s https://${API_APP_NAME}.azurewebsites.net/api/v1/ping"
echo ""
echo "Run migrations from repo (optional):"
echo "  export DATABASE_URL='(copy from Portal; password hidden above)'"
echo "  cd apps/api && PYTHONPATH=src:../../packages/common/src python3 -m alembic upgrade head"
