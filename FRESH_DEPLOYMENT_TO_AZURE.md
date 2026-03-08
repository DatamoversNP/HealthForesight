# Fresh Deployment to Azure - Complete Guide

## ✅ Everything is Ready!

All fixes and files are included. The deployment script will handle everything automatically.

## 🚀 Deploy Now

**Run this single command:**

```bash
./START_PRODUCTION_BUILD.sh
```

## 📦 What's Included (Automatically)

### API Deployment Package
✅ **All source code** - Complete API with all fixes
✅ **Logging system** - `logging_config.py`, `middleware_logging.py`
✅ **packages/common** - Shared code included
✅ **Policy files** - All policy files with embedded metadata:
   - `data/policy_*.json`
   - `data/policies/*.json`
   - `apps/api/data/policies/policy-*.json`
   - `data/valid_policies.json`
   - `data/canonical_policies.json`
✅ **Risk register** - `data/risks/` directory
✅ **requirements.txt** - All Python dependencies
✅ **startup.sh** - Azure startup script
✅ **Environment variables** - `STORAGE_PATH` set automatically

### Web Deployment Package
✅ **Production build** - Complete frontend build
✅ **Fixed logger** - localStorage quota fix included
✅ **Fixed UI** - DOM nesting warning fix included
✅ **Environment config** - API URL configured automatically

## 🔧 What the Script Does

1. **Checks prerequisites** (Azure CLI, zip)
2. **Detects existing Azure resources** (or prompts to create)
3. **Builds API package:**
   - Includes all source code
   - Includes packages/common
   - Includes all policy files
   - Includes requirements.txt
   - Creates ZIP file
4. **Deploys API** to Azure App Service
5. **Sets environment variables** (STORAGE_PATH, etc.)
6. **Builds Web package:**
   - Installs dependencies
   - Builds production bundle
   - Creates ZIP file
7. **Deploys Web** to Azure App Service
8. **Restarts services** to apply changes

## ⚙️ Configuration

The script will:
- ✅ Auto-detect existing Azure resources
- ✅ Set `STORAGE_PATH="/home/site/wwwroot/data"`
- ✅ Set `SCM_DO_BUILD_DURING_DEPLOYMENT=true`
- ✅ Configure API URL for frontend automatically
- ✅ Use `startup.sh` for API startup

## 📋 Deployment Steps

1. **Run deployment:**
   ```bash
   ./START_PRODUCTION_BUILD.sh
   ```

2. **Follow prompts:**
   - Confirm resource group (or create new)
   - Confirm API app name (or enter new)
   - Confirm Web app name (or enter new)

3. **Wait for completion:**
   - API deployment: ~2-5 minutes
   - Web deployment: ~1-3 minutes
   - Service restart: ~30 seconds

4. **Verify deployment:**
   - API: `curl https://[API_APP_NAME].azurewebsites.net/health`
   - Web: Open `https://[WEB_APP_NAME].azurewebsites.net`

## ✅ Verification Checklist

After deployment:

- [ ] API health check returns 200
- [ ] Web application loads
- [ ] Policies load correctly
- [ ] Dashboard works
- [ ] No console errors
- [ ] Logging works (check Azure logs)

## 🔍 Check Logs

**API Logs:**
```bash
az webapp log tail --resource-group [RESOURCE_GROUP] --name [API_APP_NAME]
```

**Web Logs:**
```bash
az webapp log tail --resource-group [RESOURCE_GROUP] --name [WEB_APP_NAME]
```

## 🎯 Summary

**Everything is included:**
- ✅ All code fixes
- ✅ All data files
- ✅ All dependencies
- ✅ All configuration
- ✅ Logging system
- ✅ Error tracking

**Just run:**
```bash
./START_PRODUCTION_BUILD.sh
```

**That's it!** The script handles everything automatically.

