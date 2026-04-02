# HealthForesight v3 – Fresh deployment to Azure

This deploys the application as a **new** deployment on Azure. Your **existing** deployment (e.g. `healthforesight-rg`, `healthforesight-api-9016`, `healthforesight-web-9016`) is **not** changed.

## What gets created (v3 only)

| Resource        | v3 name (default)        | Existing (unchanged)   |
|----------------|---------------------------|------------------------|
| Resource group | `healthforesight-v3-rg`   | `healthforesight-rg`   |
| API (Web App)  | `healthforesight-api-v3`  | `healthforesight-api-9016` |
| Frontend (Static Web App) | `healthforesight-web-v3` | `healthforesight-web-9016` |

Plus: new App Service plan, storage account, and file share in the v3 resource group.

## Prerequisites

- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed and logged in (`az login`)
- Node.js and npm (for frontend build)
- Repo at project root (so `scripts/azure/` and `apps/api`, `apps/web` exist)

## Step 1: Provision Azure resources (one-time)

Creates the v3 resource group and all app/storage resources:

```bash
cd /path/to/uepi-migration-20260123-151729
chmod +x scripts/azure/provision-fresh-v3.sh
./scripts/azure/provision-fresh-v3.sh
```

If an app name is already taken globally, use your own names:

```bash
export API_APP_NAME=healthforesight-api-v3-mycompany
export STATIC_WEB_APP_NAME=healthforesight-web-v3-mycompany
./scripts/azure/provision-fresh-v3.sh
```

## Step 2: Deploy API and frontend

Builds and deploys the app code to the v3 resources:

```bash
chmod +x scripts/azure/deploy-fresh-v3.sh
./scripts/azure/deploy-fresh-v3.sh
```

This runs:

1. `deploy-api.sh` – packages API + `packages/common`, deploys to the v3 Web App, sets startup and app settings.
2. `deploy-frontend.sh` – builds the web app with the v3 API URL and deploys to the v3 Static Web App.

If you used custom names in Step 1, set the same variables before deploy:

```bash
export RESOURCE_GROUP=healthforesight-v3-rg
export API_APP_NAME=healthforesight-api-v3-mycompany
export STATIC_WEB_APP_NAME=healthforesight-web-v3-mycompany
./scripts/azure/deploy-fresh-v3.sh
```

## Step 3: Verify

- **API:**  
  `curl -s https://<API_APP_NAME>.azurewebsites.net/api/v1/health`
- **Docs:**  
  `https://<API_APP_NAME>.azurewebsites.net/docs`
- **Web:**  
  Open `https://<STATIC_WEB_APP_NAME>.azurestaticapps.net` in a browser.

Replace `<API_APP_NAME>` / `<STATIC_WEB_APP_NAME>` with the names you used (e.g. `healthforesight-api-v3` and `healthforesight-web-v3`).

## Database (required for full API)

The API expects **PostgreSQL** via the `DATABASE_URL` setting. After provisioning:

1. Create an Azure Database for PostgreSQL (flexible server) **or** use an existing server and create a **new database** for v3 (e.g. `healthforesight_v3`) so the old app’s data is untouched.
2. In Azure Portal: **App Service** → your v3 API app → **Configuration** → **Application settings** → add:
   - **Name:** `DATABASE_URL`
   - **Value:** `postgresql+psycopg2://user:password@host:5432/dbname` (your PostgreSQL connection string)

Or set it via CLI:

```bash
az webapp config appsettings set \
  --resource-group healthforesight-v3-rg \
  --name healthforesight-api-v3 \
  --settings DATABASE_URL="postgresql+psycopg2://user:password@host:5432/healthforesight_v3"
```

Then run migrations (Alembic) against the new DB if needed. Any other secrets or env vars should be set in the v3 Web App’s **Configuration**.

## Summary

1. **Provision (once):** `./scripts/azure/provision-fresh-v3.sh`
2. **Deploy:** `./scripts/azure/deploy-fresh-v3.sh`
3. **Use:** v3 API and frontend URLs; existing deployment is left as-is.
