# Azure Deployment - Next Steps

## Current Status
- ✅ Azure resources created (Resource Group, Storage Account, App Service, Static Web App)
- ✅ API code deployed
- ❌ API not starting (container exits with code 2, startup probe fails)

## Problem
The container starts but the application isn't responding to health checks. This could be:
1. Module import error (`uepi_api` not found)
2. Port binding issue (wrong port)
3. Application crash on startup
4. Missing dependencies

## Immediate Actions

### 1. Enable Application Logging
```bash
./scripts/azure/enable-logging.sh
az webapp restart --resource-group healthforesight-rg --name healthforesight-api-9016
```

### 2. Check Logs via Azure Portal (Recommended)
1. Go to: https://portal.azure.com
2. Navigate: **App Services** → `healthforesight-api-9016`
3. Click: **Log stream** (real-time logs)
4. Look for Python errors, import errors, or tracebacks

### 3. Use Kudu Console to Debug
1. Go to: https://healthforesight-api-9016.scm.azurewebsites.net
2. Click: **Debug console** → **CMD**
3. Test the startup command:
   ```bash
   cd /home/site/wwwroot/src
   export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src"
   python -c "import sys; sys.path.insert(0, '/home/site/wwwroot/src'); import uepi_api.main"
   ```
4. If that works, try:
   ```bash
   python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000
   ```

### 4. Verify Deployment Structure
In Kudu console:
```bash
ls -la /home/site/wwwroot/src/uepi_api/main.py
ls -la /home/site/wwwroot/src/uepi_api/
```

## Most Likely Issues

### Issue 1: Module Not Found
**Symptom**: `ModuleNotFoundError: No module named 'uepi_api'`
**Fix**: Ensure PYTHONPATH includes `/home/site/wwwroot/src`

### Issue 2: Wrong Port
**Symptom**: App starts but health check fails
**Fix**: Use `${PORT}` environment variable instead of hardcoded `8000`

### Issue 3: Missing Dependencies
**Symptom**: Import errors for specific packages
**Fix**: Check `requirements.txt` is complete and deployed

## Alternative: Use Startup Script
The `startup.sh` script handles Azure's Oryx build system. Try:
```bash
az webapp config set \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016 \
  --startup-file "bash startup.sh"
```

## Once Fixed
After the API is working:
1. Deploy frontend: `./scripts/azure/deploy-frontend.sh`
2. Update frontend API URL
3. Test end-to-end

