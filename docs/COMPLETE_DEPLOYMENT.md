# HealthForesight – Complete deployment (same links as before)

This guide covers a **full deployment** to Azure: API, frontend, database migrations, and user seed, using the **same app names and URLs** as before.

---

## URLs (same as before)

| What       | URL |
|-----------|-----|
| **API**   | `https://healthforesight-api.azurewebsites.net` |
| **API docs** | `https://healthforesight-api.azurewebsites.net/docs` |
| **Frontend** | `https://healthforesight-web.azurestaticapps.net` (or `https://healthforesight-web.azurewebsites.net` if using App Service for web) |

---

## Prerequisites

1. **Azure CLI** – logged in (`az login`).
2. **Existing Azure resources** (same as before):
   - Resource group: `healthforesight-rg`
   - API: Web App `healthforesight-api`
   - Frontend: Static Web App (or Web App) `healthforesight-web`
   - PostgreSQL: Azure Database for PostgreSQL (Flexible Server) or your own server
3. **Database connection string** – for migrations and user seed (and for the API at runtime).
4. **Local tools** (for the deploy script):
   - Bash
   - Node.js & npm (for frontend build)
   - Python 3 (for migrations and seed)

---

## 1. Set API environment variables in Azure

The API needs at least **DATABASE_URL** so it can connect to PostgreSQL. Set it in the Azure Web App (Portal or CLI).

**Option A – Azure Portal**

1. Go to **App Service** → `healthforesight-api` → **Configuration** → **Application settings**.
2. Add or edit:
   - **Name:** `DATABASE_URL`  
   - **Value:** `postgresql://USER:PASSWORD@YOUR-SERVER.postgres.database.azure.com:5432/YOUR_DATABASE?sslmode=require`  
     (use your real server, user, password, and database name.)
3. Optionally add **JWT_SECRET** (a long random string) for production. If not set, the API uses a default (fine for dev/demo only).
4. Save.

**Option B – Azure CLI**

```bash
az webapp config appsettings set \
  --resource-group healthforesight-rg \
  --name healthforesight-api \
  --settings DATABASE_URL="postgresql://USER:PASSWORD@YOUR-SERVER.postgres.database.azure.com:5432/YOUR_DATABASE?sslmode=require"
```

Replace `USER`, `PASSWORD`, `YOUR-SERVER`, and `YOUR_DATABASE` with your PostgreSQL details.

---

## 2. One-command full deploy (from repo root)

Use the **same DATABASE_URL** (or one pointing to the same database) so migrations and seed run against the DB the API uses.

```bash
cd /path/to/uepi-migration-20260123-151729

export DATABASE_URL="postgresql://USER:PASSWORD@YOUR-SERVER.postgres.database.azure.com:5432/YOUR_DATABASE?sslmode=require"

./scripts/azure/deploy-complete-full.sh
```

The script will:

| Step | What it does |
|------|----------------------|
| **0** | Set API **CORS** so the frontend origin can call the API |
| **1** | Deploy **API** (code + startup) to `healthforesight-api` |
| **2** | Build and deploy **Frontend** to `healthforesight-web` (pointing at the API URL above) |
| **3** | Run **database migrations** (`alembic upgrade head`) |
| **4** | **Seed users** (admin and roles; password `Swan@1234`) |

No steps are skipped if `DATABASE_URL` is set.

---

## 3. Deploy without database steps

If you only want to deploy app code (no migrations, no seed):

```bash
SKIP_MIGRATIONS=1 SKIP_SEED=1 ./scripts/azure/deploy-complete-full.sh
```

You can run migrations and seed later (see below).

---

## 4. What gets deployed

- **API**
  - App code under `apps/api` and `packages/common`.
  - Startup script and PYTHONPATH so the app runs on Azure.
  - CORS updated to include the frontend URL.
- **Frontend**
  - Production build with `VITE_API_URL` = `https://healthforesight-api.azurewebsites.net/api/v1`.
  - Deployed to Azure Static Web Apps (or Web App fallback).
- **Database**
  - All Alembic migrations in `apps/api/alembic/versions/` (001 through 007).
  - Tables for tenants, users, roles, policies, analyses, baselines, observations, jobs, analytics runs, verdicts, etc.
- **Data**
  - Seeded users and roles (see below).

---

## 5. Seeded users (password for all: `Swan@1234`)

| Email | Name | Roles |
|-------|------|--------|
| demo@example.com | Demo User | POLICY_ADMIN, UM_LEADER |
| admin@healthforesight.com | Admin User | POLICY_ADMIN |
| sarah.analyst@healthforesight.com | Sarah Analyst | ACTUARIAL |
| mike.leader@healthforesight.com | Mike UM Leader | UM_LEADER |
| jane.exec@healthforesight.com | Jane Executive | EXEC_VIEWER |
| david.compliance@healthforesight.com | David Compliance | COMPLIANCE |

Open the **frontend URL** (same link as before), then sign in with **email** and **password** (e.g. `admin@healthforesight.com` / `Swan@1234`).

---

## 6. Run migrations or seed later

**Migrations only:**

```bash
cd apps/api
export DATABASE_URL="postgresql://..."
export PYTHONPATH="$(pwd)/src:$(pwd)/../../packages/common/src"
python3 -m alembic upgrade head
```

**Seed users only:**

```bash
# From repo root
export DATABASE_URL="postgresql://..."
export PYTHONPATH="apps/api/src:packages/common/src"
python3 scripts/seed_users.py
```

---

## 7. Optional: demo data (policies, etc.)

The repo includes extra scripts for demo policies/pipelines. They are **optional** and not run by the main deploy script. If you want them, run after deploy and migrations, from repo root, with `DATABASE_URL` and `PYTHONPATH` set as above:

```bash
# Example: seed policies (if you use one of these scripts)
# PYTHONPATH=apps/api/src:packages/common/src python3 apps/api/scripts/seed_policies.py
```

Use the script that matches the demo data you want; the main deployment does **not** depend on them.

---

## 8. Verify deployment

1. **API health:**  
   `curl -s https://healthforesight-api.azurewebsites.net/api/v1/health`
2. **API docs:**  
   Open `https://healthforesight-api.azurewebsites.net/docs`
3. **Frontend:**  
   Open `https://healthforesight-web.azurestaticapps.net` (or the Web App URL if you use that).
4. **Login:**  
   Sign in with one of the seeded users and password `Swan@1234`.

---

## 9. Troubleshooting

| Issue | What to do |
|-------|------------|
| Frontend can’t call API (CORS) | Ensure API App Settings include `CORS_ORIGINS` with the frontend origin (the script sets this). Or set it manually in Portal/CLI. |
| API 500 or DB errors | Check API logs: `az webapp log tail -g healthforesight-rg -n healthforesight-api`. Confirm `DATABASE_URL` is set and correct. |
| Migrations fail | Run from `apps/api` with `DATABASE_URL` and `PYTHONPATH` set; ensure the DB is reachable and empty enough for migrations. |
| Seed fails | Confirm migrations have run and `DATABASE_URL` is the same as the API. Run `scripts/seed_users.py` manually with the same env. |
| Login not found | Ensure Step 4 (seed) ran and you use one of the emails above with password `Swan@1234`. |

**Site failed to start within 10 mins:** If zip deploy keeps failing after setting `SCM_DO_BUILD_DURING_DEPLOYMENT=true`, deploy the API as a **Docker container** instead (dependencies are installed at build time, so the app starts in under a minute):

```bash
./scripts/azure/deploy-api-docker.sh
```

Prerequisites: Docker (or Docker Desktop) and Azure CLI. The script creates an Azure Container Registry if needed, builds the API image, pushes it, and configures the Web App to run that image. Keep `DATABASE_URL` and other app settings in the Web App; they are unchanged. After this, use the same API URL.

---

## Summary

- **Same links:** API at `https://healthforesight-api.azurewebsites.net`, frontend at `https://healthforesight-web.azurestaticapps.net` (or same name on .azurewebsites.net).
- **One full deploy:**  
  `export DATABASE_URL="..."; ./scripts/azure/deploy-complete-full.sh`
- **Includes:** API + frontend + CORS + migrations + user seed; no components omitted for a standard deployment.
