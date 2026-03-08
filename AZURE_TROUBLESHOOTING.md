# Azure Deployment Troubleshooting

## Current Status

- ✅ App Service: **Running**
- ⏳ API: **Not responding yet**

## Quick Diagnostics

Run this to see what's happening:

```bash
./scripts/azure/check-api-logs.sh
```

Or check logs manually:

```bash
az webapp log tail \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016
```

## Common Issues & Fixes

### Issue 1: Module Not Found

**Symptom**: `ModuleNotFoundError: No module named 'uepi_api'`

**Fix**: Update startup command and PYTHONPATH:

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
```

### Issue 2: Import Errors

**Symptom**: Import errors in logs

**Fix**: Check if all dependencies are in `requirements.txt`:

```bash
# Verify gunicorn is in requirements
grep gunicorn apps/api/requirements.txt
```

### Issue 3: File Storage Connection

**Symptom**: Errors accessing Azure File Storage

**Fix**: Verify environment variables:

```bash
az webapp config appsettings list \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016 \
  --query "[?contains(name, 'AZURE')].{name:name, value:value}"
```

### Issue 4: Port Binding

**Symptom**: App can't bind to port

**Fix**: Azure uses port 8000 by default. Verify startup command uses `0.0.0.0:8000`.

## Manual Fixes

### Fix Startup Command

```bash
az webapp config set \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016 \
  --startup-file "gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 600 --chdir /home/site/wwwroot/src uepi_api.main:app"
```

### Set PYTHONPATH

```bash
az webapp config appsettings set \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016 \
  --settings PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot"
```

### Restart App

```bash
az webapp restart \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016
```

## Check What's Actually Happening

```bash
# View real-time logs
az webapp log tail \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016

# Download logs for analysis
az webapp log download \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016 \
  --log-file api-logs.zip
```

## Expected Log Output

When working correctly, you should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

If you see errors, share them and we can fix them.

