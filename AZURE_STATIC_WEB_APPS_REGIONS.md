# Azure Static Web Apps - Available Regions

## Issue

Static Web Apps are only available in specific regions, not all Azure regions.

## Available Regions

- `westus2`
- `centralus`
- `eastus2` (closest to `eastus`)
- `westeurope`
- `eastasia`

## Solution

The migration script has been updated to automatically use `eastus2` when `eastus` is selected, since Static Web Apps are not available in `eastus`.

## Alternative: Use App Service for Frontend

If you prefer to keep everything in the same region, you can deploy the frontend to App Service instead:

```bash
# Create Web App for frontend (same region as API)
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $WEB_APP_NAME \
  --runtime "NODE:18-lts" \
  --output none
```

This allows you to use the same region (`eastus`) for both API and frontend.

