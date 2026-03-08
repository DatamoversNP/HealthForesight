# Azure Container Exit Code 2 - Diagnosis

## Problem
The container is exiting with code 2, which indicates a startup error. The deployment was successful, but the application is crashing on startup.

## What We Know
- Deployment successful (Oryx build completed)
- Dependencies installed correctly
- Container starts but exits with code 2
- No application error logs visible in standard logs

## Likely Causes

1. **Module Import Error**: `uepi_api` module not found
2. **Missing Dependencies**: Some Python packages not installed
3. **Startup Command Error**: The startup command is failing
4. **Port Binding Issue**: Port 8000 might not be available or wrong

## Next Steps

### Option 1: Check Application Logs via Azure Portal
1. Go to: https://portal.azure.com
2. Navigate: **App Services** → `healthforesight-api-9016`
3. Click: **Log stream** (real-time application logs)
4. Or: **Advanced Tools (Kudu)** → **Debug console** → **CMD** → Check `/home/site/wwwroot/src/uepi_api/`

### Option 2: Enable Detailed Logging
Enable application logging to see Python errors:

```bash
az webapp log config \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016 \
  --application-logging filesystem \
  --level verbose \
  --docker-container-logging filesystem
```

### Option 3: Test Startup Command Manually
Use Kudu console to test the startup command:
1. Go to: https://healthforesight-api-9016.scm.azurewebsites.net
2. **Debug console** → **CMD**
3. Run:
   ```bash
   cd /home/site/wwwroot/src
   export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src"
   python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000
   ```

This will show the actual error message.

### Option 4: Check if Module Exists
In Kudu console:
```bash
ls -la /home/site/wwwroot/src/uepi_api/main.py
python -c "import sys; sys.path.insert(0, '/home/site/wwwroot/src'); import uepi_api.main"
```

## Most Likely Fix

The issue is probably that the startup command needs to be in a different format or the module path is wrong. Try updating the startup command to use the startup.sh script that handles Azure's Oryx build system properly.

