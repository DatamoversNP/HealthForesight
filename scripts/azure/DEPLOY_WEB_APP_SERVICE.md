# App Service frontend + API CORS

If the UI is on **healthforesight-web.azurewebsites.net** and the API on **healthforesight-api.azurewebsites.net**, the browser blocks cross-origin calls (CORS).

The SPA **always** calls **`https://healthforesight-web.../api/v1/...`** (same origin). That only works if the **web** app runs **`server.mjs`**, which proxies `/api` → the real API. A **static-only** zip (just `dist/`) will make API calls **404** — you must deploy Node + proxy (see below).

## Deploy

```bash
# From repo root (no Static Web App token → deploys to App Service healthforesight-web)
./scripts/azure/deploy-frontend.sh
```

Or set explicitly:

```bash
export RESOURCE_GROUP=healthforesight-rg
export STATIC_WEB_APP_NAME=healthforesight-web
export API_URL=https://healthforesight-api.azurewebsites.net
./scripts/azure/deploy-frontend.sh
```

## Azure Portal (first time)

1. **Web App** → **Configuration** → **General settings**
   - **Stack**: Node 20 LTS  
   - **Startup Command**: `node server.mjs`
2. **Application settings**: `API_BACKEND_URL` = `https://healthforesight-api.azurewebsites.net` (no `/api` suffix)

## Verify

Open `https://healthforesight-web.azurewebsites.net` — Network tab should show API calls to **your web origin** `/api/v1/...`, not to `healthforesight-api...`.
