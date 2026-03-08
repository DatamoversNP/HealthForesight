# How to Check Deployment Logs in Azure Portal

## Step-by-Step Guide

### Method 1: Via Azure Portal (Recommended)

1. **Go to Azure Portal**
   - Open: https://portal.azure.com
   - Sign in if needed

2. **Navigate to Your App Service**
   - Click on **"App Services"** in the left menu (or search for it)
   - Find and click on: **`hf-api8755146`**

3. **Open Deployment Center**
   - In the left menu of your App Service, scroll down
   - Click on: **"Deployment Center"** (or "Deployment center")
   - This shows your deployment history

4. **View Deployment Logs**
   - You'll see a list of deployments
   - Find your most recent deployment (should be at the top)
   - Click on the **deployment entry** (or click on **"Logs"** or **"Show deployment logs"**)
   - This opens the deployment log viewer

5. **Read the Logs**
   - Look for **errors** (red text)
   - Look for **warnings** (yellow text)
   - Look for messages like "Build failed" or "Deployment failed"
   - Common errors to look for:
     - ModuleNotFoundError
     - ImportError
     - Build failures
     - Missing files

### Method 2: Via SCM/Kudu Site (Alternative)

1. **Go to Kudu Console**
   - Open: `https://hf-api8755146.scm.azurewebsites.net`
   - This is the SCM (Source Control Manager) site

2. **View Deployments**
   - Click on: **"Deployments"** in the top menu
   - You'll see a list of all deployments

3. **Open Deployment Logs**
   - Click on your most recent deployment
   - Click on **"View log"** or click on the deployment entry
   - This shows detailed deployment logs

4. **Alternative: Check Log Files**
   - Click: **"Debug console"** → **"Bash"** or **"PowerShell"**
   - Navigate: `cd /home/LogFiles` (Linux) or `cd D:\home\LogFiles` (Windows)
   - Check log files:
     ```bash
     # List log files
     ls -la
     
     # View deployment log
     cat deployment*.log
     
     # Or view last deployment log
     cat $(ls -t deployment*.log | head -1)
     ```

### Method 3: Via Azure CLI

```bash
# List deployments
az webapp deployment list \
  --name hf-api8755146 \
  --resource-group healthforesight-rg \
  --output table

# Get latest deployment log
az webapp log download \
  --name hf-api8755146 \
  --resource-group healthforesight-rg \
  --log-file deployment-logs.zip

# Extract and view
unzip deployment-logs.zip
cat deployment*.log
```

## What to Look For in Logs

### Common Errors:

1. **ModuleNotFoundError**
   ```
   ModuleNotFoundError: No module named 'uepi_api'
   ```
   - **Issue**: PYTHONPATH not set or wrong directory structure
   - **Fix**: Check if `src/uepi_api/` exists in deployment

2. **Build Failures**
   ```
   Failed to install dependencies
   ERROR: Could not find a version that satisfies the requirement
   ```
   - **Issue**: Missing or incorrect requirements.txt
   - **Fix**: Check requirements.txt is included and valid

3. **Missing Files**
   ```
   startup.sh: No such file or directory
   ```
   - **Issue**: startup.sh not included in deployment ZIP
   - **Fix**: Ensure startup.sh is in the ZIP

4. **Permission Errors**
   ```
   startup.sh: Permission denied
   ```
   - **Issue**: startup.sh not executable
   - **Fix**: Set executable: `chmod +x startup.sh`

5. **Import Errors**
   ```
   ImportError: cannot import name 'main' from 'uepi_api'
   ```
   - **Issue**: main.py not found or wrong structure
   - **Fix**: Check `src/uepi_api/main.py` exists

## Quick Navigation Paths

### Azure Portal Path:
```
Azure Portal
→ App Services (search or click)
→ hf-api8755146
→ Deployment Center (left menu)
→ Logs (or click on deployment)
```

### Kudu/SCM Path:
```
https://hf-api8755146.scm.azurewebsites.net
→ Deployments (top menu)
→ Click on deployment
→ View log
```

### Direct Log Files:
```
https://hf-api8755146.scm.azurewebsites.net
→ Debug console → Bash
→ cd /home/LogFiles
→ ls -la
→ cat deployment*.log
```

## Screenshot Guide

### In Azure Portal:
1. **Left Menu** → Scroll down → **"Deployment Center"**
2. **Main Panel** → Shows deployment history
3. **Click on deployment** → Shows log viewer
4. **Scroll through logs** → Look for errors

### In Kudu:
1. **Top Menu** → Click **"Deployments"**
2. **Deployment List** → Shows all deployments
3. **Click deployment** → Shows details
4. **Click "View log"** → Shows deployment logs

## Alternative: Check Application Logs

If deployment logs don't show errors, check application logs:

```bash
# Enable application logging
az webapp log config \
  --name hf-api8755146 \
  --resource-group healthforesight-rg \
  --application-logging filesystem \
  --level verbose \
  --output none

# Stream logs
az webapp log tail \
  --name hf-api8755146 \
  --resource-group healthforesight-rg
```

Then check logs at:
- Azure Portal → Your App → **Log stream**
- Or: `https://hf-api8755146.scm.azurewebsites.net/api/logs/docker`

## Summary

**Easiest Method:**
1. Azure Portal → App Services → `hf-api8755146`
2. Left menu → **"Deployment Center"**
3. Click on your deployment → View logs

**Direct Link:**
- Deployment Center: `https://portal.azure.com/#@/resource/subscriptions/YOUR_SUB/resourceGroups/healthforesight-rg/providers/Microsoft.Web/sites/hf-api8755146/deploymentCenter`

**Kudu Console:**
- `https://hf-api8755146.scm.azurewebsites.net` → Deployments

**Check these logs first - they'll show you exactly what went wrong during deployment!**
