# Azure Migration Fix - Linux App Service

## Issue Fixed

The migration script was trying to create a Windows App Service for Python, which is not supported. The fix:

1. **App Service Plan**: Added `--is-linux` flag
2. **Web App**: Added `--os-type Linux` flag
3. **Startup Command**: Configured gunicorn for Linux
4. **Dependencies**: Added gunicorn to requirements.txt

## Updated Script

The `scripts/azure/migrate-to-azure.sh` script has been updated to:

```bash
# Create Linux App Service Plan
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku B1 \
  --is-linux \  # ← Added this
  --output none

# Create Linux Web App
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $API_APP_NAME \
  --runtime "PYTHON:3.11" \
  --os-type Linux \  # ← Added this
  --output none
```

## Next Steps

1. **Delete the failed resources** (if any were created):
   ```bash
   az group delete --name healthforesight-rg --yes --no-wait
   ```

2. **Run the fixed migration script**:
   ```bash
   ./scripts/azure/migrate-to-azure.sh
   ```

The script will now correctly create a Linux-based App Service for Python.

## Verification

After running the script, verify the App Service is Linux:

```bash
az webapp show \
  --name $API_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "{os:kind, runtime:siteConfig.linuxFxVersion}"
```

You should see:
- `os`: "app,linux"
- `runtime`: "PYTHON|3.11"

