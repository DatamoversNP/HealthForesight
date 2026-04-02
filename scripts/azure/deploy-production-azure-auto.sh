#!/usr/bin/env bash
# =============================================================================
# One-shot production deploy: resolve DATABASE_URL + REDIS_URL via Azure CLI,
# then run deploy-production-stack.sh.
#
# Prerequisites: az login, PostgreSQL + Redis + Web App + ACR in the resource group.
#
# DB password is never returned by Azure — provide:
#   export POSTGRES_PASSWORD='your-admin-password'
# or the script prompts (hidden).
#
# Optional: RESOURCE_GROUP, POSTGRES_SERVER_NAME, POSTGRES_DB_NAME, REDIS_CACHE_NAME,
#           API_APP_NAME, SKIP_FRONTEND, SKIP_WORKER, SKIP_MIGRATIONS, SKIP_SEED, JWT_SECRET
#
# Redis (if none in the resource group):
#   export REDIS_URL='rediss://:KEY@name.redis.cache.windows.net:6380/0'   # skip discovery
#   OR create Basic C0 in this RG:
#   export PROVISION_REDIS=1
#   export REDIS_NEW_NAME=my-unique-redis-name   # must be exported or child script won't see it
#   ./scripts/azure/deploy-production-azure-auto.sh
#   (Redis names are globally unique in Azure.)
#
# Usage (repo root):
#   export POSTGRES_PASSWORD='...'
#   ./scripts/azure/deploy-production-azure-auto.sh
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api}"
POSTGRES_DB_NAME="${POSTGRES_DB_NAME:-postgres}"

if ! command -v az &>/dev/null; then
  echo "ERROR: Azure CLI (az) not found."
  exit 1
fi

if ! az account show &>/dev/null; then
  echo "ERROR: Run: az login"
  exit 1
fi

if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 required for URL-encoding passwords."
  exit 1
fi

_urlencode() {
  python3 -c 'import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=""))' "$1"
}

# --- PostgreSQL ---
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
  if ! resolve_postgres "$POSTGRES_SERVER_NAME"; then
    echo "ERROR: No server '$POSTGRES_SERVER_NAME' in $RESOURCE_GROUP (flexible or single)."
    exit 1
  fi
else
  NF=$(az postgres flexible-server list --resource-group "$RESOURCE_GROUP" --query "length(@)" -o tsv 2>/dev/null || echo 0)
  if [[ "$NF" =~ ^[0-9]+$ ]] && [[ "$NF" -eq 1 ]]; then
    POSTGRES_SERVER_NAME=$(az postgres flexible-server list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv)
    resolve_postgres "$POSTGRES_SERVER_NAME" || exit 1
    echo "Using PostgreSQL Flexible Server: $POSTGRES_SERVER_NAME"
  elif [[ "$NF" =~ ^[0-9]+$ ]] && [[ "$NF" -gt 1 ]]; then
    PICK=""
    while IFS= read -r line; do
      [[ -z "$line" ]] && continue
      if echo "$line" | grep -qi postgres || echo "$line" | grep -qi uepi; then
        PICK="$line"
        break
      fi
    done < <(az postgres flexible-server list --resource-group "$RESOURCE_GROUP" --query "[].name" -o tsv)
    if [[ -z "$PICK" ]]; then
      PICK=$(az postgres flexible-server list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv)
    fi
    resolve_postgres "$PICK" || exit 1
    echo "Using PostgreSQL Flexible Server (auto-pick): $POSTGRES_SERVER_NAME"
  else
    NS=$(az postgres server list --resource-group "$RESOURCE_GROUP" --query "length(@)" -o tsv 2>/dev/null || echo 0)
    if [[ "$NS" =~ ^[0-9]+$ ]] && [[ "$NS" -eq 1 ]]; then
      POSTGRES_SERVER_NAME=$(az postgres server list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv)
      resolve_postgres "$POSTGRES_SERVER_NAME" || exit 1
      echo "Using PostgreSQL Single Server: $POSTGRES_SERVER_NAME"
    else
      echo "ERROR: No single flexible server and no usable single server in $RESOURCE_GROUP."
      echo "Create PostgreSQL or set POSTGRES_SERVER_NAME."
      exit 1
    fi
  fi
fi

# --- Redis ---
REDIS_HOST=""
REDIS_KEY=""
USE_PRESET_REDIS_URL=""

if [[ -n "${REDIS_URL:-}" ]]; then
  if [[ "$REDIS_URL" != *"REDIS_ACCESS_KEY"* ]] && [[ "$REDIS_URL" != *"YOURNAME.redis.cache.windows.net"* ]]; then
    USE_PRESET_REDIS_URL=1
    echo "Using REDIS_URL from environment (skipping Azure Redis discovery)."
  fi
fi

if [[ -z "$USE_PRESET_REDIS_URL" ]]; then
  if [[ -n "${REDIS_CACHE_NAME:-}" ]]; then
    REDIS_HOST=$(az redis show --resource-group "$RESOURCE_GROUP" --name "$REDIS_CACHE_NAME" --query hostName -o tsv 2>/dev/null || true)
    if [[ -z "$REDIS_HOST" ]]; then
      echo "ERROR: Redis '$REDIS_CACHE_NAME' not found in $RESOURCE_GROUP."
      exit 1
    fi
    REDIS_KEY=$(az redis list-keys --resource-group "$RESOURCE_GROUP" --name "$REDIS_CACHE_NAME" --query primaryKey -o tsv)
  else
    NR=$(az redis list --resource-group "$RESOURCE_GROUP" --query "length(@)" -o tsv 2>/dev/null || echo 0)
    if [[ "$NR" =~ ^[0-9]+$ ]] && [[ "$NR" -eq 1 ]]; then
      REDIS_CACHE_NAME=$(az redis list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv)
      REDIS_HOST=$(az redis show --resource-group "$RESOURCE_GROUP" --name "$REDIS_CACHE_NAME" --query hostName -o tsv)
      REDIS_KEY=$(az redis list-keys --resource-group "$RESOURCE_GROUP" --name "$REDIS_CACHE_NAME" --query primaryKey -o tsv)
      echo "Using Redis: $REDIS_CACHE_NAME"
    elif [[ "$NR" =~ ^[0-9]+$ ]] && [[ "$NR" -gt 1 ]]; then
      RPICK=""
      while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        if echo "$line" | grep -qi redis || echo "$line" | grep -qi uepi; then
          RPICK="$line"
          break
        fi
      done < <(az redis list --resource-group "$RESOURCE_GROUP" --query "[].name" -o tsv)
      if [[ -z "$RPICK" ]]; then
        RPICK=$(az redis list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv)
      fi
      REDIS_CACHE_NAME="$RPICK"
      REDIS_HOST=$(az redis show --resource-group "$RESOURCE_GROUP" --name "$REDIS_CACHE_NAME" --query hostName -o tsv)
      REDIS_KEY=$(az redis list-keys --resource-group "$RESOURCE_GROUP" --name "$REDIS_CACHE_NAME" --query primaryKey -o tsv)
      echo "Using Redis (auto-pick): $REDIS_CACHE_NAME"
    else
      if [[ "${PROVISION_REDIS:-}" == "1" ]]; then
        LOC=$(az group show --name "$RESOURCE_GROUP" --query location -o tsv)
        RNEW="${REDIS_NEW_NAME:-}"
        if [[ -z "$RNEW" ]]; then
          # Short random suffix — Redis DNS names must be globally unique.
          RNEW="hf$(python3 -c 'import secrets; print(secrets.token_hex(4))')"
        fi
        echo "No Redis in $RESOURCE_GROUP — creating Azure Cache for Redis '$RNEW' (Basic C0) in $LOC ..."
        echo "This can take several minutes."
        az redis create \
          --location "$LOC" \
          --name "$RNEW" \
          --resource-group "$RESOURCE_GROUP" \
          --sku Basic \
          --vm-size c0 \
          --output none
        REDIS_CACHE_NAME="$RNEW"
        REDIS_HOST=$(az redis show --resource-group "$RESOURCE_GROUP" --name "$REDIS_CACHE_NAME" --query hostName -o tsv)
        REDIS_KEY=$(az redis list-keys --resource-group "$RESOURCE_GROUP" --name "$REDIS_CACHE_NAME" --query primaryKey -o tsv)
        echo "Redis created: $REDIS_CACHE_NAME ($REDIS_HOST)"
      else
        echo "ERROR: No Azure Cache for Redis in resource group '$RESOURCE_GROUP'."
        echo ""
        echo "Pick one:"
        echo "  A) Create cache automatically (Basic C0, ~\$ cheap tier; name must be globally unique):"
        echo "       export REDIS_NEW_NAME=your-unique-redis-name"
        echo "       export PROVISION_REDIS=1"
        echo "       $0"
        echo "     (omit REDIS_NEW_NAME to auto-generate hfxxxxxxxx)"
        echo ""
        echo "  B) Create 'Azure Cache for Redis' in Portal in this resource group, then re-run deploy-full."
        echo ""
        echo "  C) Use an existing cache elsewhere — paste full URL:"
        echo "       export REDIS_URL='rediss://:PRIMARY_KEY@HOSTNAME.redis.cache.windows.net:6380/0'"
        echo "       $0"
        exit 1
      fi
    fi
  fi
fi

RAW_PASS="${POSTGRES_PASSWORD:-${DATABASE_PASSWORD:-}}"
if [[ -z "$RAW_PASS" ]]; then
  read -r -s -p "PostgreSQL admin password (user ${PG_USER}): " RAW_PASS
  echo ""
fi
if [[ -z "$RAW_PASS" ]]; then
  echo "ERROR: Empty password."
  exit 1
fi

ENC_USER=$(_urlencode "$PG_USER")
ENC_PASS=$(_urlencode "$RAW_PASS")
DATABASE_URL="postgresql://${ENC_USER}:${ENC_PASS}@${PG_FQDN}:5432/${POSTGRES_DB_NAME}?sslmode=require"

if [[ -z "$USE_PRESET_REDIS_URL" ]]; then
  ENC_KEY=$(_urlencode "$REDIS_KEY")
  REDIS_URL="rediss://:${ENC_KEY}@${REDIS_HOST}:6380/0"
fi

if [[ -z "${JWT_SECRET:-}" ]]; then
  EXISTING_JWT=$(az webapp config appsettings list --resource-group "$RESOURCE_GROUP" --name "$API_APP_NAME" \
    --query "[?name=='JWT_SECRET'].value" -o tsv 2>/dev/null | head -1 || true)
  if [[ -n "$EXISTING_JWT" && "$EXISTING_JWT" != "null" ]]; then
    JWT_SECRET="$EXISTING_JWT"
    echo "Reusing JWT_SECRET from Web App $API_APP_NAME."
  else
    if command -v openssl &>/dev/null; then
      JWT_SECRET=$(openssl rand -base64 48)
    else
      JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")
    fi
    echo "Generated new JWT_SECRET."
  fi
fi

export DATABASE_URL REDIS_URL JWT_SECRET
unset PRODUCTION_ENV_FILE

echo ""
echo "Resolved (resource group: $RESOURCE_GROUP):"
echo "  PostgreSQL ($PG_KIND): $POSTGRES_SERVER_NAME  $PG_FQDN  database=$POSTGRES_DB_NAME"
if [[ -n "$USE_PRESET_REDIS_URL" ]]; then
  echo "  Redis: from REDIS_URL env"
else
  echo "  Redis: ${REDIS_CACHE_NAME:-?}  ${REDIS_HOST:-?}"
fi
echo ""

exec "$SCRIPT_DIR/deploy-production-stack.sh"
