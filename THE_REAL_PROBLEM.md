# The Real Problem: ImagePullFailure

## What I Found

The logs show:
```
Container pull image failed with reason: ImagePullFailure.
```

This is **NOT** a ContainerCreateFailure - it's **ImagePullFailure**. Azure App Service cannot authenticate to ACR to pull the Docker image.

## Why This Happens

1. **ACR Admin Access Not Enabled**: By default, ACR admin access is disabled. App Service needs it enabled to use admin credentials.

2. **Password Not Set Correctly**: Even if set, the password might not be in the right format or the credentials might have expired.

3. **Authentication Method**: Azure App Service uses admin credentials, not managed identity (unless configured).

## The Fix

Run this script - it will:

1. ✅ Enable ACR admin access (required)
2. ✅ Get fresh ACR credentials  
3. ✅ Set credentials using modern Azure CLI commands
4. ✅ Also set them in app settings as backup
5. ✅ Restart the app

```bash
./FIX_ACR_AUTHENTICATION.sh
```

## What Makes This Different from Local

| Local | Azure App Service |
|-------|------------------|
| You run `az acr login` → Docker uses your Azure CLI session | App Service needs **admin credentials** stored in settings |
| Your credentials are active in your session | Azure needs **explicit admin username/password** |
| Works automatically | Requires **admin access enabled** on ACR |

## Manual Fix (If Script Fails)

1. **Enable Admin Access:**
   ```bash
   az acr update --name healthforesightacr12666 --admin-enabled true
   ```

2. **Get Credentials:**
   ```bash
   az acr credential show --name healthforesightacr12666
   ```

3. **Set in App Service:**
   ```bash
   az webapp config container set \
     --name hf-api8755146 \
     --resource-group healthforesight-rg \
     --container-image-name healthforesightacr12666.azurecr.io/uepi-api:latest \
     --container-registry-url https://healthforesightacr12666.azurecr.io \
     --container-registry-user healthforesightacr12666 \
     --container-registry-password "PASSWORD_FROM_STEP_2"
   ```

4. **Restart:**
   ```bash
   az webapp restart --name hf-api8755146 --resource-group healthforesight-rg
   ```

This is the **concrete fix** for ImagePullFailure.
