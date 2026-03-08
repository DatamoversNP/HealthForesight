# Deployment Verification Checklist

## ✅ Pre-Deployment Verification

### Code Fixes Included
- [x] localStorage quota fix (`apps/web/src/lib/logger.ts`)
- [x] DOM nesting warning fix (`apps/web/src/pages/persona/ExecutiveDashboardPage.tsx`)
- [x] Logging system (`apps/api/src/uepi_api/logging_config.py`)
- [x] Request logging middleware (`apps/api/src/uepi_api/middleware_logging.py`)
- [x] Frontend logger (`apps/web/src/lib/logger.ts`)

### Files to Deploy

#### API Files
- [x] All API source code (`apps/api/src/`)
- [x] `requirements.txt` with all dependencies
- [x] `startup.sh` for Azure
- [x] `packages/common/src/` (shared code)
- [x] Policy files with embedded metadata:
  - `data/policy_*.json`
  - `data/policies/*.json`
  - `apps/api/data/policies/policy-*.json`
  - `data/valid_policies.json`
  - `data/canonical_policies.json`
- [x] Risk register data (`data/risks/`)

#### Web Files
- [x] All web source code (`apps/web/src/`)
- [x] Production build (`apps/web/dist/`)
- [x] Environment configuration (`.env.production`)

### Environment Variables
- [x] `STORAGE_PATH="/home/site/wwwroot/data"`
- [x] `SCM_DO_BUILD_DURING_DEPLOYMENT=true`
- [x] `VITE_API_URL` (set automatically)

### Dependencies
- [x] Python dependencies in `requirements.txt`
- [x] Node.js dependencies (built into `dist/`)

## 🚀 Deployment Command

```bash
./START_PRODUCTION_BUILD.sh
```

## ✅ Post-Deployment Verification

### API Verification
1. **Health Check:**
   ```bash
   curl https://[API_APP_NAME].azurewebsites.net/health
   ```
   Expected: `{"status":"healthy","service":"uepi-api"}`

2. **Check Logs:**
   ```bash
   az webapp log tail --resource-group [RESOURCE_GROUP] --name [API_APP_NAME]
   ```
   Look for: "Application startup complete"

3. **Test Policies Endpoint:**
   ```bash
   curl https://[API_APP_NAME].azurewebsites.net/api/v1/policies
   ```
   Expected: Array of policies

### Web Verification
1. **Access Web App:**
   ```
   https://[WEB_APP_NAME].azurewebsites.net
   ```

2. **Check Browser Console:**
   - No localStorage quota errors
   - No DOM nesting warnings
   - API calls succeed

3. **Test Features:**
   - Policies load
   - Dashboard loads
   - Policy workspace loads
   - No console errors

## 📋 What's Included in Deployment

### API Package Includes:
- ✅ All Python source code
- ✅ `packages/common` shared code
- ✅ Policy files (all locations)
- ✅ Risk register data
- ✅ `requirements.txt`
- ✅ `startup.sh`
- ✅ Logging system files
- ✅ All routers and middleware

### Web Package Includes:
- ✅ Production build (`dist/`)
- ✅ All static assets
- ✅ Environment configuration
- ✅ Fixed logger code
- ✅ Fixed UI components

## ⚠️ Important Notes

1. **Data Files:** Policy files with embedded metadata are included from:
   - `data/policy_*.json`
   - `data/policies/*.json`
   - `apps/api/data/policies/policy-*.json`

2. **Environment Variables:** `STORAGE_PATH` is automatically set to `/home/site/wwwroot/data`

3. **Dependencies:** Python dependencies are installed during deployment via `SCM_DO_BUILD_DURING_DEPLOYMENT=true`

4. **Startup:** Uses `startup.sh` which handles path detection automatically

## 🔧 Troubleshooting

If deployment fails:

1. **Check Azure Logs:**
   ```bash
   az webapp log tail --resource-group [RESOURCE_GROUP] --name [API_APP_NAME]
   ```

2. **Verify ZIP Contents:**
   ```bash
   unzip -l api-deployment.zip | grep -E "(main.py|requirements.txt|packages/common)"
   ```

3. **Check Environment Variables:**
   ```bash
   az webapp config appsettings list --resource-group [RESOURCE_GROUP] --name [API_APP_NAME]
   ```

4. **Verify Data Files:**
   ```bash
   az webapp ssh --resource-group [RESOURCE_GROUP] --name [API_APP_NAME]
   ls -la /home/site/wwwroot/data/
   ```

