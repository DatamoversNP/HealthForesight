# Fix: Azure App Service Startup Failure

## Problem

Deployment failed because the worker process failed to start within 10 minutes:
```
Error: Deployment for site 'hf-api8755146' with DeploymentId '41631926-e4e5-45d0-b19a-49d21e68f711' failed because the worker proccess failed to start within the allotted time.
```

## Root Causes

Common reasons for startup failures:

1. **PYTHONPATH not set correctly** - Azure can't find `uepi_api` module
2. **Wrong startup command** - Command doesn't work in Azure environment
3. **Missing dependencies** - Required packages not installed
4. **Wrong directory structure** - Code not in expected location
5. **Port configuration** - Should use `$PORT` environment variable

## Solution

I've updated the deployment script to fix these issues:

### 1. Startup Command Configuration

**Before:**
```bash
--startup-file "python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000"
```

**After:**
```bash
--startup-file "startup.sh"
```

With `startup.sh` containing:
```bash
#!/bin/bash
export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"
cd /home/site/wwwroot
python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### 2. PYTHONPATH Configuration

Azure App Service needs explicit PYTHONPATH:
- `/home/site/wwwroot/src` - Where `uepi_api` module is located
- `/home/site/wwwroot/packages/common/src` - Common packages (if needed)

### 3. Port Configuration

Azure provides `PORT` environment variable:
- Use `${PORT:-8000}` instead of hardcoded `8000`
- Falls back to `8000` if PORT not set

### 4. Directory Structure

The deployment ZIP should have:
```
/home/site/wwwroot/
├── src/
│   └── uepi_api/
│       └── main.py
├── requirements.txt
├── startup.sh
└── .deployment
```

## Checking Logs

### Via Azure Portal

1. Go to: https://portal.azure.com
2. Navigate: **App Services** → Your API App
3. Click: **Log stream** (real-time logs)
4. Or: **Logs** → **Application Logging**

### Via SCM Site

1. Go to: `https://<your-api-app-name>.scm.azurewebsites.net/api/logs/docker`
2. Or: `https://<your-api-app-name>.scm.azurewebsites.net/logstream`

### Via Azure CLI

```bash
# Stream logs
az webapp log tail \
  --name <your-api-app-name> \
  --resource-group healthforesight-rg

# Download logs
az webapp log download \
  --name <your-api-app-name> \
  --resource-group healthforesight-rg \
  --log-file logs.zip
```

## Common Startup Errors

### "ModuleNotFoundError: No module named 'uepi_api'"

**Solution:**
- Check PYTHONPATH is set correctly
- Verify `src/uepi_api/` exists in deployment ZIP
- Check startup script includes PYTHONPATH

### "Cannot find module 'uvicorn'"

**Solution:**
- Verify `requirements.txt` includes `uvicorn[standard]`
- Check build logs for installation errors
- Re-deploy with updated requirements.txt

### "Port 8000 already in use"

**Solution:**
- Use `${PORT:-8000}` instead of hardcoded port
- Azure App Service provides PORT environment variable

### "Failed to start within 10 minutes"

**Solution:**
- Check application logs for errors
- Verify startup command is correct
- Check if app is actually starting (look for "Application startup complete")

## Manual Fix

If you want to manually fix the current deployment:

### Step 1: Check Current Configuration

```bash
az webapp config show \
  --name <your-api-app-name> \
  --resource-group healthforesight-rg \
  --query linuxFxVersion
```

### Step 2: Set Startup Command

```bash
az webapp config set \
  --name <your-api-app-name> \
  --resource-group healthforesight-rg \
  --startup-file "startup.sh"
```

### Step 3: Create Startup Script

Create a file in Azure App Service (via Kudu or upload):
- Path: `/home/site/wwwroot/startup.sh`
- Content:
```bash
#!/bin/bash
export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"
cd /home/site/wwwroot
python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### Step 4: Set PYTHONPATH in App Settings

```bash
az webapp config appsettings set \
  --name <your-api-app-name> \
  --resource-group healthforesight-rg \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none
```

### Step 5: Restart App

```bash
az webapp restart \
  --name <your-api-app-name> \
  --resource-group healthforesight-rg
```

## Alternative: Use App Settings for PYTHONPATH

You can also set PYTHONPATH via App Settings:

```bash
az webapp config appsettings set \
  --name <your-api-app-name> \
  --resource-group healthforesight-rg \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none
```

Then startup command can be simpler:
```bash
python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

## Verify Deployment Structure

Check what's actually deployed:

### Via Kudu Console

1. Go to: `https://<your-api-app-name>.scm.azurewebsites.net`
2. Click: **Debug console** → **PowerShell** or **Bash**
3. Navigate: `cd /home/site/wwwroot`
4. Check structure: `ls -la` or `dir`

### Via Azure CLI

```bash
# List files (if available via API)
az webapp deployment source config-zip \
  --resource-group healthforesight-rg \
  --name <your-api-app-name> \
  --src <your-zip-file> \
  --debug
```

## Recommended Deployment Structure

For Azure App Service, the deployment should have:

```
/home/site/wwwroot/
├── src/
│   └── uepi_api/
│       ├── __init__.py
│       ├── main.py
│       └── ... (all other modules)
├── requirements.txt
├── startup.sh
└── .deployment
```

## Testing Locally

Before deploying, test the startup command locally:

```bash
# Set PYTHONPATH
export PYTHONPATH="apps/api/src:packages/common/src:$PYTHONPATH"

# Test startup
cd apps/api/src
python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000
```

## Next Steps

1. **Re-run deployment** with updated script
2. **Check logs** for specific errors
3. **Verify PYTHONPATH** is set correctly
4. **Test startup** command manually if needed

## Summary

✅ **Startup script created** - Proper PYTHONPATH and PORT configuration
✅ **Startup command updated** - Uses startup.sh file
✅ **PYTHONPATH configured** - Points to correct directories
✅ **Port configuration fixed** - Uses ${PORT:-8000}
✅ **Ready to redeploy** - Script will include startup.sh in ZIP

**Re-run the deployment script - it should now start correctly!**
