# Azure Startup Fix

## Issue
API is deployed but not responding. The startup command needs to use `startup.sh` which handles Azure's Oryx build system.

## Solution

The `startup.sh` script is designed to work with Azure's deployment system. It:
1. Finds the Oryx-extracted directory
2. Sets PYTHONPATH correctly
3. Starts uvicorn with the correct configuration

## Apply Fix

Run the updated fix script:

```bash
./scripts/azure/fix-api-startup.sh
```

Or manually:

```bash
# Set PYTHONPATH
az webapp config appsettings set \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016 \
  --settings PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src"

# Use startup.sh script
az webapp config set \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016 \
  --startup-file "bash startup.sh"

# Restart
az webapp restart \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016
```

## Check Logs

After restart, check logs to see startup messages:

```bash
az webapp log tail \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016
```

Look for:
- `[STARTUP] Using extracted directory: ...`
- `[STARTUP] Starting uvicorn on port 8000...`
- `INFO:     Application startup complete.`

## Alternative: Use Gunicorn Directly

If startup.sh doesn't work, try gunicorn with correct paths:

```bash
az webapp config set \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016 \
  --startup-file "cd /home/site/wwwroot && PYTHONPATH=/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 600 --chdir src uepi_api.main:app"
```

