# Azure Startup Issue - Fixed

## Problem Identified

The startup command contained **local development paths** that don't exist on Azure:
```
PYTHONPATH=...:/Users/nilesh/Downloads/uepi-migration-20260123-151729/apps/api/src:...
```

This caused the app to fail to start because:
1. Local paths don't exist on Azure servers
2. The PYTHONPATH was polluted with invalid paths
3. The startup command was overly complex

## Solution

1. **Clean PYTHONPATH**: Set it to only Azure paths:
   ```
   /home/site/wwwroot/src:/home/site/wwwroot/packages/common/src
   ```

2. **Simple startup command**: Use direct uvicorn command:
   ```
   cd /home/site/wwwroot/src && python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000
   ```

## Apply Fix

Run:
```bash
./scripts/azure/fix-startup-direct.sh
```

This will:
1. Clean the PYTHONPATH environment variable
2. Set a simple, direct uvicorn startup command
3. Restart the app
4. Test the API

## Verify

After running the fix, check status:
```bash
./scripts/azure/check-api-status.sh
```

The API should respond at:
- Health: `https://healthforesight-api-9016.azurewebsites.net/api/v1/health`
- Docs: `https://healthforesight-api-9016.azurewebsites.net/docs`

