# Complete Startup Solution - All Issues Fixed

## The Problem

We've been dealing with multiple issues:
1. ✅ CORS errors (fixed)
2. ✅ Missing scipy dependency (will be installed)
3. ❌ Manual server management (now automated)
4. ❌ Unreliable startup (now fixed)

## The Solution

I've created a **complete startup script** that handles everything automatically.

## How to Use (Simple!)

### Start Everything:
```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
./start-both-servers.sh
```

### Stop Everything:
```bash
./stop-both-servers.sh
```

## What the Script Does

### ✅ Step 1: Python Environment
- Creates virtual environment (if needed)
- Installs ALL dependencies including:
  - FastAPI, Uvicorn
  - scipy, numpy (for predicted impact)
  - All other required packages

### ✅ Step 2: Clean Shutdown
- Stops any existing servers on ports 8000 and 3050
- Ensures clean startup

### ✅ Step 3: Data Files
- Copies required data files

### ✅ Step 4: API Server
- Starts API server on port 8000
- Verifies it's responding
- Waits for full startup

### ✅ Step 5: Web Server
- Installs npm dependencies (if needed)
- Starts web server on port 3050
- Verifies it's responding
- Waits for full startup

## Features

- ✅ **Automatic dependency installation**
- ✅ **Both servers start in correct order**
- ✅ **Verification at each step**
- ✅ **Clean shutdown of existing servers**
- ✅ **Comprehensive CORS configuration**
- ✅ **Single command to start everything**

## Expected Output

When you run `./start-both-servers.sh`, you'll see:

```
🚀 Starting HealthForesight Application
📦 Step 1: Setting up Python environment...
   ✅ Virtual environment activated
   ✅ Python packages installed
🛑 Step 2: Stopping any existing servers...
   ✅ API server stopped
   ✅ Web server stopped
🌐 Step 4: Starting API server...
   ✅ API server is responding!
🖥️  Step 5: Starting Web server...
   ✅ Web server is responding!
✅ SUCCESS! Both servers are starting!
```

## Access Points

- **Web Application**: http://localhost:3050
- **API Server**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Time Estimate

- **First run**: 3-4 minutes (installs all dependencies)
- **Subsequent runs**: 30-60 seconds (everything cached)

## Troubleshooting

### If something goes wrong:

1. **Check logs**:
   ```bash
   tail -f api-server.log
   tail -f web-server.log
   ```

2. **Stop everything and restart**:
   ```bash
   ./stop-both-servers.sh
   ./start-both-servers.sh
   ```

3. **Manual check**:
   ```bash
   curl http://localhost:8000/health  # API
   curl http://localhost:3050          # Web
   ```

## Summary

**One script to rule them all!** 🎯

Just run:
```bash
./start-both-servers.sh
```

And everything will be set up correctly with all dependencies installed and both servers running.

No more manual steps, no more missing dependencies, no more CORS issues!
