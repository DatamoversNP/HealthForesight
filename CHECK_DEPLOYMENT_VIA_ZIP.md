# Check Deployment Logs When Deployed via ZIP

## Issue

Deployment Center → Logs tab is empty because you deployed via ZIP upload (not CI/CD), so logs don't show there.

## Where to Find Logs

Since you deployed using `az webapp deployment source config-zip`, the logs are in different places:

### Method 1: Check Kudu Console (Recommended)

1. **Go to Kudu Console:**
   - Open: `https://hf-api8755146.scm.azurewebsites.net`

2. **Check Deployments Tab:**
   - Click: **"Deployments"** in the top menu
   - This shows ZIP deployments (different from CI/CD deployments)

3. **Check Log Files:**
   - Click: **"Debug console"** → **"Bash"** (or PowerShell)
   - Navigate to log files:
     ```bash
     cd /home/LogFiles
     ls -la
     ```

4. **View Deployment Logs:**
   ```bash
   # List all log files
   ls -la
   
   # View deployment log
   cat deployment*.log
   
   # Or view latest
   cat $(ls -t deployment*.log | head -1)
   ```

### Method 2: Check What Was Actually Deployed

1. **Go to Kudu Console:**
   - `https://hf-api8755146.scm.azurewebsites.net`

2. **Check File Structure:**
   - Click: **"Debug console"** → **"Bash"**
   - Navigate: `cd /home/site/wwwroot`
   - Check structure:
     ```bash
     ls -la
     ls -la src/
     ls -la src/uepi_api/
     ```

3. **Verify Files Exist:**
   ```bash
   # Check if main.py exists
   ls -la src/uepi_api/main.py
   
   # Check if requirements.txt exists
   ls -la requirements.txt
   
   # Check if startup.sh exists
   ls -la startup.sh
   ```

### Method 3: Check Application Logs (Startup Errors)

Since the app didn't start, check application logs:

1. **Enable Application Logging:**
   ```bash
   az webapp log config \
     --name hf-api8755146 \
     --resource-group healthforesight-rg \
     --application-logging filesystem \
     --level verbose
   
   az webapp restart \
     --name hf-api8755146 \
     --resource-group healthforesight-rg
   ```

2. **Check Log Stream:**
   - Azure Portal → Your App → **Log stream**
   - Or: `https://hf-api8755146.scm.azurewebsites.net/api/logs/docker`

3. **Check Log Files:**
   ```bash
   # Via Kudu console
   cd /home/LogFiles
   cat default_docker.log
   cat application.log
   ```

### Method 4: Test Startup Manually (See Exact Error)

1. **Go to Kudu Console:**
   - `https://hf-api8755146.scm.azurewebsites.net`
   - Click: **"Debug console"** → **"Bash"**

2. **Test Startup:**
   ```bash
   cd /home/site/wwwroot
   
   # Set PYTHONPATH
   export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"
   
   # Test import
   python -c "import uepi_api.main; print('Import OK')"
   
   # Test startup (this will show the exact error)
   python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000
   ```

   **This will show you the exact error preventing startup!**

## Quick Diagnostic Commands

Run these in Kudu Bash console:

```bash
# 1. Check file structure
cd /home/site/wwwroot
ls -la

# 2. Check if src/uepi_api exists
ls -la src/uepi_api/

# 3. Check if main.py exists
ls -la src/uepi_api/main.py

# 4. Check if requirements.txt exists
cat requirements.txt | head -20

# 5. Check if startup.sh exists and is executable
ls -la startup.sh
cat startup.sh

# 6. Test Python import
python -c "import sys; print(sys.path)"
export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"
python -c "import uepi_api.main; print('OK')"

# 7. Check installed packages
pip list | grep -i fastapi
pip list | grep -i uvicorn

# 8. Test startup (shows exact error)
python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000
```

## What to Look For

### Common Issues:

1. **Missing `src/uepi_api/main.py`**
   - Check: `ls -la src/uepi_api/main.py`
   - Fix: Ensure ZIP includes `src/uepi_api/` directory

2. **Missing `startup.sh`**
   - Check: `ls -la startup.sh`
   - Fix: Ensure startup.sh is in ZIP root

3. **startup.sh not executable**
   - Check: `ls -la startup.sh` (should show `-rwxr-xr-x`)
   - Fix: `chmod +x startup.sh`

4. **Dependencies not installed**
   - Check: `pip list | grep fastapi`
   - Fix: Check requirements.txt was included

5. **PYTHONPATH not set**
   - Check: `python -c "import sys; print(sys.path)"`
   - Fix: Set in startup.sh or app settings

## Next Steps

1. **Go to Kudu Console** (easiest way to diagnose):
   - `https://hf-api8755146.scm.azurewebsites.net`
   - Click: **Debug console** → **Bash**

2. **Run diagnostic commands** (listed above)

3. **Test startup manually** (command #8 above)
   - This will show you the exact error

4. **Share the error** and we can fix it!

## Summary

✅ **Deployment Center logs empty** - Normal for ZIP deployments
✅ **Check Kudu Console** - Shows actual deployment files and logs
✅ **Test startup manually** - Shows exact error preventing startup
✅ **Check file structure** - Verify all files were deployed correctly

**Go to Kudu Console and run the diagnostic commands - that will show you what's wrong!**
