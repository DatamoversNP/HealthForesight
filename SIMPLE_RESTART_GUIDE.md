# Simple Guide: How to Restart the API Server

## Quick Summary

The API server is a Python application that runs on port 8000. You need to restart it so it loads the new code we added.

## Step-by-Step Instructions

### 1. Find the API Server Process

The API is likely running in one of these places:
- **A terminal window** (most common) - Look for a window showing `uvicorn` or `FastAPI` output
- **Background process** - Running in the background

### 2. Stop the API Server

**If running in a terminal:**
- Go to that terminal window
- Press `Ctrl+C` (or `Cmd+C` on Mac)
- This will stop the server

**If you can't find the terminal:**
- Open a new terminal
- Run: `lsof -i :8000` (finds what's using port 8000)
- Find the PID (process ID) number
- Run: `kill <PID>` (replace <PID> with the number)

### 3. Start the API Server Again

Open a terminal and run:

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution/apps/api"
uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 4. Verify It's Working

- Open browser: http://localhost:8000/docs
- Or test: http://localhost:8000/api/v1/health

### 5. Test Predicted Impact

- Go to: http://localhost:3050/policies
- Click the Psychology icon (🧠) on any policy
- Predicted impact should now display!

## Why Restart Was Needed

We added a new method `get_policy()` to the storage adapter code. The API needs to restart to load this new code.

## Project Structure (Simple Explanation)

```
Your Project/
├── apps/
│   ├── api/          ← API Server (Python/FastAPI) - Port 8000
│   ├── web/          ← Frontend (React) - Port 3050  
│   └── worker/       ← Background Jobs (Python/Celery)
│
├── packages/
│   └── common/       ← Shared code used by API and Worker
│
└── data/             ← Data files (JSON policies, etc.)
```

**How it works:**
1. **Frontend (web)** - What you see in the browser
2. **API (api)** - Handles requests from frontend, reads/writes data
3. **Worker** - Does heavy calculations in the background

The API server we're restarting is the middle layer that connects the frontend to the data.
