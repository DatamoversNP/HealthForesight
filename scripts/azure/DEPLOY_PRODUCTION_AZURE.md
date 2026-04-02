# Production-like Azure deployment

**Single entry point (help / fix-db / deploy-full / verify):** `scripts/azure/healthforesight-azure-master.sh help`

This path matches what the codebase expects for **reliable** elasticity, daily jobs, and heavy SQL: **API + Redis + Celery worker**, plus tuned Postgres timeouts.

## What gets deployed

| Piece | Role |
|--------|------|
| **API Web App** (Linux container) | `deploy-api-docker.sh` — Gunicorn, `PG_STATEMENT_TIMEOUT_MS`, `REDIS_URL`, `DATABASE_URL` |
| **Worker Web App** (Linux container) | Celery consumer; same DB/Redis/storage settings as API |
| **Azure Cache for Redis** | Celery broker/backend (`REDIS_URL`) |
| **PostgreSQL** | `DATABASE_URL` |
| **Frontend** (optional) | `deploy-frontend.sh` → Static Web App |

## Prerequisites

1. **Azure CLI**: `az login`
2. **Resource group** with an existing **Linux** API Web App and **Azure Container Registry** (the API Docker flow you already use).
3. **Azure Database for PostgreSQL** — connection string with `sslmode=require`.
4. **Azure Cache for Redis** (Basic C0+ is enough to start). In the portal: **Access keys** → primary connection string, or build:
   - `rediss://:<Primary access key>@<name>.redis.cache.windows.net:6380/0`
   - The API client adjusts `ssl_cert_reqs` for `rediss://` when needed.

## One-command stack (recommended)

1. Copy the template and edit **`production.azure.env`** in an editor (VS Code, nano, etc.). Set **`DATABASE_URL`**, **`REDIS_URL`**, and **`JWT_SECRET`** to real values from the Azure Portal.  
   **Do not** paste lines that start with `#` into the shell (zsh will try to run `#` as a command and print `command not found: #`).

   ```bash
   cp scripts/azure/production.azure.env.example scripts/azure/production.azure.env
   ```

2. From the **repo root** (one line):

   ```bash
   PRODUCTION_ENV_FILE=scripts/azure/production.azure.env ./scripts/azure/deploy-production-stack.sh
   ```

The script **refuses** template placeholders such as `HOST.postgres.database.azure.com` or `REDIS_ACCESS_KEY` so you do not deploy broken connection strings by mistake.

### Fully automated URL resolution (recommended)

If PostgreSQL and Redis are already in the same resource group as the Web App, run:

```bash
export POSTGRES_PASSWORD='your-azure-postgres-admin-password'
./scripts/azure/deploy-production-azure-auto.sh
```

This script uses `az` to discover server hostnames, Redis keys, builds `DATABASE_URL` / `REDIS_URL`, reuses or generates `JWT_SECRET`, then runs `deploy-production-stack.sh`.  
Omit `POSTGRES_PASSWORD` to be prompted (input hidden).

Optional: `POSTGRES_SERVER_NAME`, `REDIS_CACHE_NAME`, `POSTGRES_DB_NAME` (default `postgres`), `RESOURCE_GROUP`.

Options:

- `SKIP_FRONTEND=1` — API + worker only  
- `SKIP_WORKER=1` — API only (not production-complete for async jobs)  
- `SKIP_MIGRATIONS=1` / `SKIP_SEED=1` — skip DB steps  

## What this sets (fixes included)

- **`REDIS_URL`** on API and worker — Celery tasks run off the API process.
- **`PG_STATEMENT_TIMEOUT_MS`** default **180000** (3 minutes) on API and worker — reduces spurious cancellations; heavy routes still use `SET LOCAL` where implemented.
- **`CORS_ORIGINS`** — Static Web App + localhost for dev.
- **Worker image** — includes `apps/api/src` (required for `uepi_api` imports), PDF/PPTX export deps, and an **Azure health** helper: a tiny HTTP listener on `PORT` so the worker Web App stays healthy while Celery runs.

## Verify

```bash
curl -s "https://<API_APP_NAME>.azurewebsites.net/api/v1/ping"
az webapp log tail -g <RESOURCE_GROUP> -n <WORKER_APP_NAME>
```

In worker logs you should see Celery **ready** and task names registered. Trigger elasticity or a daily job; API logs should **not** show `Celery enqueue failed` if Redis is reachable.

## Cost / scale notes

- Run API and worker on at least **Basic** or **Standard** plans if you need **Always On** and predictable CPU.
- For very large tenants, scale the **worker** (separate plan or larger SKU) before the API.

## Related scripts

- `deploy-api-docker.sh` — API image only (used by the stack script).
- `deploy-frontend.sh` — Static Web Apps build with `VITE_API_URL`.
- `deploy-complete-full.sh` — lighter path without Redis/worker automation.
