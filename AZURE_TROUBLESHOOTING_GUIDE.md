# Azure API Troubleshooting Guide

## Current Status
- ✅ Azure resources created
- ✅ Code deployed (with packages/common)
- ❌ API not starting

## Common Issues and Solutions

### Issue 1: startup.sh not found
**Symptom**: `bash: startup.sh: No such file or directory`

**Solution**: Use direct command instead of script file:
```bash
./scripts/azure/fix-startup-simple.sh
```

### Issue 2: Module not found (uepi_common)
**Symptom**: `ModuleNotFoundError: No module named 'uepi_common'`

**Solution**: Ensure packages/common is in deployment:
- Check that `packages/common/src` is in the zip
- Verify PYTHONPATH includes `/home/site/wwwroot/packages/common/src`

### Issue 3: CORS_ORIGINS parsing error
**Symptom**: `pydantic_settings.exceptions.SettingsError: error parsing value for field "cors_origins"`

**Solution**: Fixed in config.py with validator - redeploy

### Issue 4: Oryx build not finding files
**Symptom**: `WARNING: Could not find virtual environment directory`

**Solution**: This is normal - Oryx extracts to /tmp. The startup command should find it.

## Next Steps

1. **Check Log Stream** in Azure Portal:
   - Look for `[STARTUP]` messages
   - Look for Python errors or tracebacks
   - Check if uvicorn starts

2. **Try Simple Startup**:
   ```bash
   ./scripts/azure/fix-startup-simple.sh
   ```

3. **Verify Deployment Structure**:
   - Use Kudu console: https://healthforesight-api-9016.scm.azurewebsites.net
   - Check: `/home/site/wwwroot/src/uepi_api/main.py` exists
   - Check: `/home/site/wwwroot/packages/common/src/uepi_common/` exists

4. **Manual Test**:
   - In Kudu console, try:
     ```bash
     cd /home/site/wwwroot/src
     export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src"
     python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000
     ```

## Expected Success Logs
```
[STARTUP] Using extracted directory: /tmp/...
[STARTUP] Starting uvicorn on port 8000...
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

