# Azure Deployment Status Check

## Deployment In Progress

The deployment is still running. The CLI timed out, but the deployment continues in the background.

## Quick Status Check

### Option 1: Check via Script

```bash
./scripts/azure/check-deployment-status.sh
```

### Option 2: Manual Check

```bash
# Check app status
az webapp show \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016 \
  --query "{state:state, defaultHostName:defaultHostName}"

# Check recent deployments
az webapp deployment list \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016 \
  --query "[0].{status:status, message:message}"

# Test API
curl https://healthforesight-api-9016.azurewebsites.net/api/v1/health
```

### Option 3: Check Deployment Portal

Visit the deployment URL:
```
https://healthforesight-api-9016.scm.azurewebsites.net/api/deployments/ae901d57-a2d6-4f3a-b32e-1e0f093342f5
```

Or check all deployments:
```
https://healthforesight-api-9016.scm.azurewebsites.net/api/deployments
```

## Check Logs

If the deployment seems stuck or you want to see what's happening:

```bash
# Real-time logs
az webapp log tail \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016

# Download logs
az webapp log download \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016 \
  --log-file api-logs.zip
```

## Common Issues

### 1. Build Taking Too Long

First deployments can take 10-15 minutes. This is normal because:
- Installing Python dependencies
- Building the application
- Setting up the environment

**Solution**: Wait a bit longer, then check status again.

### 2. Startup Command Issues

If the app fails to start, check the startup command:

```bash
az webapp config show \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016 \
  --query "{startup:linuxFxVersion,command:appCommandLine}"
```

Should show:
- `startup`: `PYTHON|3.11`
- `command`: `gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 600 uepi_api.main:app`

### 3. Missing Dependencies

If you see import errors in logs, check `requirements.txt` includes all dependencies.

### 4. File Storage Connection

Verify Azure File Storage settings:

```bash
az webapp config appsettings list \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016 \
  --query "[?name=='USE_AZURE_FILE_STORAGE' || name=='AZURE_STORAGE_ACCOUNT_NAME']"
```

## Next Steps

1. **Wait 5-10 more minutes** for deployment to complete
2. **Check status** using the script or manual commands above
3. **Test API** once deployment shows as successful
4. **Deploy frontend** once API is confirmed working

## Expected Timeline

- **First deployment**: 10-15 minutes (normal)
- **Subsequent deployments**: 3-5 minutes (faster)

The deployment is likely still building. Give it a few more minutes, then check the status again.

