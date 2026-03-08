# Quick Fix for API Not Responding

## Issue
App is "Running" but API is not responding. This is usually a PYTHONPATH or startup command issue.

## Quick Fix

Run this script to fix the startup configuration:

```bash
./scripts/azure/fix-api-startup.sh
```

This will:
1. Set PYTHONPATH correctly
2. Update startup command with correct paths
3. Restart the app
4. Test if API responds

## Manual Fix (if script doesn't work)

```bash
# Set PYTHONPATH
az webapp config appsettings set \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016 \
  --settings PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot"

# Update startup command
az webapp config set \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016 \
  --startup-file "gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 600 --chdir /home/site/wwwroot/src uepi_api.main:app"

# Restart
az webapp restart \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016
```

## Check Logs

After fixing, check logs to see if it's working:

```bash
az webapp log tail \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016
```

You should see:
```
INFO:     Started server process
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Test API

```bash
curl https://healthforesight-api-9016.azurewebsites.net/api/v1/health
```

If you see a response, the API is working!

