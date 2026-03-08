# Debug: Azure App Service "No Instances Found"

## Problem

Log Stream shows "No instances found" - this means the app failed to start completely. No worker processes are running.

## Debugging Steps

### Step 1: Check Deployment Logs

The runtime logs (Log Stream) show nothing because the app never started. Check the **deployment/build logs** instead:

**Via Azure Portal:**
1. Go to: https://portal.azure.com
2. Navigate: **App Services** → `hf-api8755146`
3. Click: **Deployment Center** → **Logs**
4. Look for build errors

**Via SCM Site:**
1. Go to: `https://hf-api8755146.scm.azurewebsites.net`
2. Click: **Debug console** → **PowerShell** or **Bash**
3. Navigate to: `D:\home\LogFiles` (Windows) or `/home/LogFiles` (Linux)
4. Check deployment logs

**Via Deployment History:**
1. Go to: `https://hf-api8755146.scm.azurewebsites.net`
2. Click: **Deployments** → Find your deployment
3. Click on the deployment to see logs

### Step 2: Check Kudu Console (What Was Actually Deployed)

Verify the deployment structure:

1. Go to: `https://hf-api8755146.scm.azurewebsites.net`
2. Click: **Debug console** → **Bash** (since it's Linux)
3. Navigate: `cd /home/site/wwwroot`
4. Check structure: `ls -la`

**Expected structure:**
```
/home/site/wwwroot/
├── src/
│   └── uepi_api/
│       ├── main.py
│       └── ...
├── requirements.txt
├── startup.sh
└── .deployment
```

**Check:**
- Does `src/uepi_api/main.py` exist?
- Does `requirements.txt` exist?
- Does `startup.sh` exist and is it executable? (`chmod +x startup.sh`)
- Check file permissions: `ls -la startup.sh`

### Step 3: Check Application Logging Settings

Enable application logging:

```bash
az webapp log config \
  --name hf-api8755146 \
  --resource-group healthforesight-rg \
  --application-logging filesystem \
  --level verbose \
  --output none

# Restart app
az webapp restart \
  --name hf-api8755146 \
  --resource-group healthforesight-rg
```

Then check logs at: `https://hf-api8755146.scm.azurewebsites.net/api/logs/docker`

### Step 4: Test Startup Command Manually

Via Kudu Console:

1. Go to: `https://hf-api8755146.scm.azurewebsites.net`
2. Click: **Debug console** → **Bash**
3. Navigate: `cd /home/site/wwwroot`
4. Test PYTHONPATH: `export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"`
5. Test import: `python -c "import uepi_api.main; print('OK')"`
6. Test startup: `python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000`

**If import fails:**
- Check if `src/uepi_api/__init__.py` exists
- Check if all required modules are in place

**If startup fails:**
- Check error message
- Look for missing dependencies
- Check port binding issues

### Step 5: Check App Settings

Verify all required settings are configured:

```bash
az webapp config appsettings list \
  --name hf-api8755146 \
  --resource-group healthforesight-rg \
  --output table
```

**Check for:**
- `PYTHONPATH` - Should be set
- `USE_AZURE_FILE_STORAGE` - Should be true
- `AZURE_STORAGE_ACCOUNT_NAME` - Should be set
- `AZURE_STORAGE_ACCOUNT_KEY` - Should be set
- `AZURE_STORAGE_FILE_SHARE_NAME` - Should be set
- `PORT` - Azure provides this automatically

### Step 6: Check Startup Command Configuration

Verify startup command is set correctly:

```bash
az webapp config show \
  --name hf-api8755146 \
  --resource-group healthforesight-rg \
  --query linuxFxVersion
```

**Should show:** Python version or startup command

Check startup file:

```bash
az webapp config show \
  --name hf-api8755146 \
  --resource-group healthforesight-rg \
  --query "linuxFxVersion" -o tsv
```

## Common Issues

### Issue 1: Missing `src/uepi_api/` Directory

**Symptom:** ImportError: No module named 'uepi_api'

**Check:**
```bash
# Via Kudu console
cd /home/site/wwwroot
ls -la src/
ls -la src/uepi_api/
```

**Fix:** The deployment ZIP structure must include `src/uepi_api/main.py`

### Issue 2: startup.sh Not Executable or Not Found

**Symptom:** "startup.sh: Permission denied" or "startup.sh: No such file"

**Check:**
```bash
# Via Kudu console
ls -la /home/site/wwwroot/startup.sh
cat /home/site/wwwroot/startup.sh
```

**Fix:** Make executable: `chmod +x /home/site/wwwroot/startup.sh`

### Issue 3: Dependencies Not Installed

**Symptom:** ImportError: No module named 'fastapi' or other dependencies

**Check:**
```bash
# Via Kudu console
pip list | grep fastapi
pip list | grep uvicorn
```

**Fix:** Check if `requirements.txt` was included and if build process installed dependencies

### Issue 4: PORT Environment Variable

**Symptom:** Port binding errors

**Check:**
```bash
# Via Kudu console
echo $PORT
env | grep PORT
```

**Fix:** Use `${PORT:-8000}` in startup command

## Quick Fixes

### Fix 1: Manually Set Startup Command

```bash
az webapp config set \
  --name hf-api8755146 \
  --resource-group healthforesight-rg \
  --startup-file "startup.sh"
```

### Fix 2: Set PYTHONPATH in App Settings

```bash
az webapp config appsettings set \
  --name hf-api8755146 \
  --resource-group healthforesight-rg \
  --settings \
    PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src" \
  --output none
```

### Fix 3: Create startup.sh Manually (via Kudu)

1. Go to: `https://hf-api8755146.scm.azurewebsites.net`
2. Click: **Debug console** → **Bash**
3. Navigate: `cd /home/site/wwwroot`
4. Create startup.sh:
```bash
cat > startup.sh <<'EOF'
#!/bin/bash
export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"
cd /home/site/wwwroot
python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port ${PORT:-8000}
EOF
chmod +x startup.sh
```

### Fix 4: Test Startup Manually (via Kudu)

```bash
# Via Kudu Bash console
cd /home/site/wwwroot
export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"
python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000
```

This will show the exact error preventing startup.

## Next Steps

1. **Check deployment logs** - See what actually happened during deployment
2. **Check Kudu console** - Verify file structure and test manually
3. **Test startup manually** - Run the startup command in Kudu to see exact errors
4. **Re-deploy if needed** - After fixing issues, re-run deployment script

## Summary

"No instances found" means the app never started. Check:
- ✅ Deployment logs (not runtime logs)
- ✅ Kudu console for file structure
- ✅ Startup script exists and is executable
- ✅ Test startup manually to see exact error
- ✅ Verify PYTHONPATH and dependencies

**Start by checking the deployment logs and Kudu console - that will show you the exact issue!**
