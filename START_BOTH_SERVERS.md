# Quick Start Guide - Both Servers

## Overview
You need **TWO terminals** running:
1. **Terminal 1**: Frontend server (port 3050) ✅ Already running
2. **Terminal 2**: API server (port 8000) ❌ Needs to be started

## Step 1: Start API Server

**Open a NEW terminal window** and run:

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
./START_API_SERVER.sh
```

### If the script doesn't work, try manually:

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729/apps/api

# Set Python path
export PYTHONPATH="/Users/nilesh/Downloads/uepi-migration-20260123-151729/apps/api/src:/Users/nilesh/Downloads/uepi-migration-20260123-151729/packages/common/src:$PYTHONPATH"

# Start the server
python3 -m uvicorn uepi_api.main:app --reload --port 8000
```

## Step 2: Verify API Server is Running

You should see output like:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Step 3: Test the API

Open a browser and go to:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Step 4: Access the Application

Once both servers are running:
- **Frontend**: http://localhost:3050
- **Product Manual**: http://localhost:3050/product-manual
- **API**: http://localhost:8000

## Troubleshooting

### If you get "ModuleNotFoundError: No module named 'uepi_api'"
Make sure you're in the correct directory and PYTHONPATH is set correctly.

### If you get "Address already in use"
Port 8000 is already in use. Stop the existing process:
```bash
lsof -ti:8000 | xargs kill -9
```

### If you get Python import errors
Check that all dependencies are installed:
```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729/apps/api
pip3 install -r requirements.txt
```

## Summary

**Keep both terminals open:**
- Terminal 1: Frontend (npm run dev) - Port 3050
- Terminal 2: API (uvicorn) - Port 8000

The console errors will disappear once the API server is running!

