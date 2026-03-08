# Fix: Azure App Service Build Failure

## Problem

Deployment failed because the build process failed. Azure App Service couldn't install Python dependencies.

## Root Cause

Azure App Service's build system (Oryx) needs a `requirements.txt` file to install Python dependencies, but the deployment only included `pyproject.toml` (Poetry format). Azure doesn't automatically convert Poetry projects to pip requirements.

## Solution

Updated the deployment script to:

1. ✅ **Generate requirements.txt** from pyproject.toml using Poetry
2. ✅ **Include requirements.txt** in the deployment ZIP
3. ✅ **Create proper startup script** for Azure
4. ✅ **Use correct PYTHONPATH** for Azure App Service
5. ✅ **Use newer deployment command** (`az webapp deploy`)

## What Changed

### 1. Generate requirements.txt

Before deployment, the script now:
- Checks if Poetry is installed
- Exports dependencies: `poetry export -f requirements.txt --output requirements.txt`
- Creates fallback requirements.txt if Poetry fails

### 2. Proper File Structure

The deployment ZIP now includes:
- ✅ `requirements.txt` - For pip install
- ✅ `src/` directory - Your application code
- ✅ `startup.sh` - Startup script with correct PYTHONPATH
- ✅ `.deployment` - Azure build configuration

### 3. PYTHONPATH Configuration

The startup script sets:
```bash
export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"
```

This ensures Azure App Service can find your modules.

## Next Steps

### Option 1: Re-run Deployment Script (Recommended)

The script is now fixed. Just run it again:

```bash
./DEPLOY_TO_AZURE.sh
```

When prompted for deployment, choose option 1 (ZIP deployment). The script will now:
1. Generate requirements.txt automatically
2. Create proper deployment package
3. Deploy to Azure

### Option 2: Manual Fix

If you want to fix the current deployment manually:

```bash
cd apps/api

# Generate requirements.txt
poetry export -f requirements.txt --output requirements.txt --without-hashes

# Create startup script
cat > startup.sh <<'EOF'
#!/bin/bash
export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"
python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000
EOF
chmod +x startup.sh

# Create deployment ZIP
zip -r deploy.zip . \
  -x "*.git*" \
  -x "*.venv*" \
  -x "*__pycache__*" \
  -x "*.pyc" \
  -x "data/*" \
  -x "target_data_model/*" \
  -x "tests/*"

# Deploy
az webapp deploy \
  --resource-group healthforesight-rg \
  --name <your-api-app-name> \
  --src-path deploy.zip \
  --type zip
```

## Checking Build Logs

If deployment still fails, check the build logs:

1. **Via Azure Portal:**
   - Go to: https://portal.azure.com
   - Navigate: App Services → Your API App
   - Click: "Deployment Center" → "Logs"

2. **Via SCM Site:**
   - Go to: `https://<your-api-app-name>.scm.azurewebsites.net/deployments`
   - Or: `https://<your-api-app-name>.scm.azurewebsites.net/logstream`

3. **Via Azure CLI:**
   ```bash
   az webapp log tail \
     --name <your-api-app-name> \
     --resource-group healthforesight-rg
   ```

## Common Build Errors

### "No module named 'uepi_api'"

**Solution:** Ensure PYTHONPATH is set correctly in startup command or startup.sh

### "ModuleNotFoundError: No module named 'packages'"

**Solution:** Make sure `packages/common/src` is included in deployment and PYTHONPATH

### "Failed to install dependency"

**Solution:** Check requirements.txt is valid and all dependencies are listed

### "Port 8000 already in use"

**Solution:** Azure App Service uses PORT environment variable, update startup command:
```bash
python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

## Verification

After deployment, verify it's working:

```bash
# Check app status
az webapp show \
  --name <your-api-app-name> \
  --resource-group healthforesight-rg \
  --query state

# Check logs
az webapp log tail \
  --name <your-api-app-name> \
  --resource-group healthforesight-rg

# Test health endpoint
curl https://<your-api-app-name>.azurewebsites.net/health
```

## Summary

✅ **Script updated** - Now generates requirements.txt automatically
✅ **Proper file structure** - Includes all necessary files
✅ **Correct PYTHONPATH** - Azure can find your modules
✅ **Ready to deploy** - Re-run the script and it should work!

**The deployment script is now fixed and ready to deploy successfully!**
