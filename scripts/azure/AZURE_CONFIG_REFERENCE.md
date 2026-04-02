# Azure App Service — actual configs (HealthForesight)

Defaults used in repo scripts. Replace **only** the secrets and Postgres host with yours.

| Setting | Value |
|--------|--------|
| Resource group | `healthforesight-rg` |
| API Web App | `healthforesight-api` |
| Web (UI) Web App | `healthforesight-web` |
| ACR (Docker API) | `healthforesightacr` |
| API public URL | `https://healthforesight-api.azurewebsites.net` |
| Web public URL | `https://healthforesight-web.azurewebsites.net` |

---

## 1. `healthforesight-api` (FastAPI — Docker image from ACR)

### General / Stack (Portal → Configuration)

| Field | Value |
|--------|--------|
| **Publish** | Docker Container |
| **Image** | `healthforesightacr.azurecr.io/healthforesight-api:latest` (your ACR name may differ) |
| **Startup command** | *(empty — do **not** use `startup.sh`)* |

### Application settings (Portal → Configuration → Application settings)

| Name | Value / notes |
|------|----------------|
| `DATABASE_URL` | `postgresql://ADMIN_USER:PASSWORD@YOUR_SERVER.postgres.database.azure.com:5432/DATABASE_NAME?sslmode=require` — **use your real server, user, password, DB**; URL-encode special chars in password |
| `WEBSITES_PORT` | *(optional; often auto)* `8000` if the platform expects it |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `false` for pure Docker (or omit) |

**Optional (recommended):**

| Name | Example |
|------|---------|
| `JWT_SECRET` | Long random string (same across restarts) |
| `ENVIRONMENT` | `production` |
| `LOG_LEVEL` | `INFO` |

**Do not** set a bogus `CORS_ORIGINS` JSON that breaks parsing; if unsure, omit or use a comma list the API accepts.

### CLI (apply API settings + clear startup)

```bash
az login
RG=healthforesight-rg
API=healthforesight-api

# Clear startup so Docker CMD runs (fixes 503 if Portal had startup.sh)
az webapp config set -g "$RG" -n "$API" --startup-command ""

# Example: set DB (paste YOUR connection string)
az webapp config appsettings set -g "$RG" -n "$API" --settings \
  'DATABASE_URL=postgresql://USER:PASS@server.postgres.database.azure.com:5432/dbname?sslmode=require'

az webapp restart -g "$RG" -n "$API"
```

---

## 2. `healthforesight-web` (Node — SPA + `/api` proxy)

### General / Stack

| Field | Value |
|--------|--------|
| **Stack** | Node **20 LTS** |
| **Startup command** | `node server.mjs` |

### Application settings

| Name | Value |
|------|--------|
| `API_BACKEND_URL` | `https://healthforesight-api.azurewebsites.net` *(no trailing slash; no `/api`)* |
| `WEBSITE_NODE_DEFAULT_VERSION` | `~20` |

### CLI

```bash
RG=healthforesight-rg
WEB=healthforesight-web

az webapp config appsettings set -g "$RG" -n "$WEB" --settings \
  "API_BACKEND_URL=https://healthforesight-api.azurewebsites.net" \
  "WEBSITE_NODE_DEFAULT_VERSION=~20"

az webapp config set -g "$RG" -n "$WEB" --linux-fx-version "NODE|20-lts"
az webapp config set -g "$RG" -n "$WEB" --startup-command "node server.mjs"

az webapp restart -g "$RG" -n "$WEB"
```

Deploy the **zip** built by `./scripts/azure/deploy-web-appservice-full.sh` (includes `server.mjs`, `dist/`, `node_modules`).

---

## 3. PostgreSQL (Azure Database for PostgreSQL)

| Setting | Value |
|--------|--------|
| **Firewall** | Allow **Azure services** *or* add **Outbound IPs** of `healthforesight-api` (App Service → Properties) |
| **SSL** | Required → use `?sslmode=require` in `DATABASE_URL` |

---

## 4. Quick health checks

```bash
# API (direct)
curl -s "https://healthforesight-api.azurewebsites.net/api/v1/health"
curl -s "https://healthforesight-api.azurewebsites.net/api/v1/ping"

# Through web proxy (same origin as browser)
curl -s "https://healthforesight-web.azurewebsites.net/api/v1/ping"
curl -s "https://healthforesight-web.azurewebsites.net/api/v1/health/detailed"
```

---

## 5. Seeded login (after `seed-azure-db.sh`)

| Email | Password |
|-------|----------|
| `admin@healthforesight.com` | `Swan@1234` |

`DATABASE_URL` for local seed must match the API app’s `DATABASE_URL` (copy from Portal).

---

## 6. Redeploy commands (from repo root)

```bash
./scripts/azure/redeploy-all.sh              # API Docker + Web Node
./scripts/azure/redeploy-all.sh --api-only
./scripts/azure/redeploy-all.sh --web-only
```
