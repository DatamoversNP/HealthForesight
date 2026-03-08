# API Server Start Guide

## Current Issue

The API server is not responding to health checks. This could be due to:
1. Server crashed during startup
2. Missing dependencies (cryptography)
3. Syntax/import errors preventing startup

## Quick Fix Steps

### Step 1: Stop Any Existing Process
```bash
lsof -ti:8000 | xargs kill -9
```

### Step 2: Install Missing Dependencies
```bash
source .venv/bin/activate
pip install cryptography
```

### Step 3: Start Server Manually (to see errors)
```bash
cd apps/api
source ../../.venv/bin/activate
export PYTHONPATH="src:../../packages/common/src:$PYTHONPATH"
python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000
```

### Step 4: Or Use Setup Script (after fixing dependencies)
```bash
./setup-venv-and-start-api.sh
```

## Fixed Issues

✅ **Indentation Error** - Fixed in main.py
✅ **Import Errors** - Fixed STORAGE_PATH exports
✅ **Dependencies** - cryptography added to setup script

## Expected Output

Once server starts successfully, you should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Verification

After server starts, test with:
```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy","service":"uepi-api"}`

## If Still Not Working

Check the terminal output for error messages. Common issues:
1. **Missing cryptography**: Install with `pip install cryptography`
2. **Import errors**: Check PYTHONPATH is set correctly
3. **Port conflicts**: Make sure nothing else is using port 8000
