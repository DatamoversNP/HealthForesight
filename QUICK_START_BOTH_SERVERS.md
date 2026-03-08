# Quick Start Guide - Both Servers

## Current Status

✅ **API Server**: Running on port 8000
⏳ **Web Server**: Starting on port 3050

## How to Start Both Servers

### Option 1: Using the Scripts (Recommended)

**Terminal 1 - API Server:**
```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
./setup-venv-and-start-api.sh
```

**Terminal 2 - Web Server:**
```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
./START_WEB_SERVER.sh
```

### Option 2: Manual Start

**API Server:**
```bash
cd apps/api
source ../../.venv/bin/activate
export PYTHONPATH="src:../../packages/common/src:$PYTHONPATH"
python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000
```

**Web Server:**
```bash
cd apps/web
npm install  # First time only
npm run dev
```

## Verification

### Check API Server:
```bash
curl http://localhost:8000/health
```
Should return: `{"status":"healthy","service":"uepi-api"}`

### Check Web Server:
Open in browser: http://localhost:3050

Or check with curl:
```bash
curl http://localhost:3050
```

## Troubleshooting

### If API server not responding:
1. Check logs: `tail -f api-server.log`
2. Restart: `./setup-venv-and-start-api.sh`

### If Web server not responding:
1. Check if port 3050 is free: `lsof -ti:3050`
2. Stop existing process: `lsof -ti:3050 | xargs kill -9`
3. Restart: `./START_WEB_SERVER.sh`

### If application still doesn't load:
1. Check browser console for errors (F12 → Console)
2. Check Network tab for failed requests
3. Verify API server is accessible: `curl http://localhost:8000/health`

## Access Points

- **Application**: http://localhost:3050
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Expected Wait Time

- **API Server**: 15-20 seconds to fully start
- **Web Server**: 10-15 seconds to fully start

Once both are running, the application should load at http://localhost:3050
