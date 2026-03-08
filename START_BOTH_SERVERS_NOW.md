# Quick Fix: Start Both Servers

## Current Status

✅ **API Server**: Running on port 8000  
❌ **Web Server**: NOT running on port 3050

## The Problem

The API server is running, but the **web server (frontend) is not running**. That's why the application isn't loading.

## Solution: Start the Web Server

### Option 1: Using the Script (Easiest)

Open a **NEW terminal window** and run:

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
./START_WEB_SERVER.sh
```

### Option 2: Manual Start

1. Open Terminal
2. Run these commands:

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution/apps/web"
npm install  # Only needed first time
npm run dev
```

## What to Expect

You should see output like:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3050/
  ➜  Network: use --host to expose
```

## Access Your Application

Once the web server starts, open your browser to:
**http://localhost:3050**

## Important Notes

1. **Keep BOTH terminal windows open**:
   - Terminal 1: API server (port 8000) - already running ✅
   - Terminal 2: Web server (port 3050) - **you need to start this**

2. **The web server needs to keep running** - don't close the terminal

3. **If you see errors**, make sure Node.js is installed:
   ```bash
   node --version
   npm --version
   ```

## Quick Check

After starting the web server, wait 10-15 seconds, then:
- Open http://localhost:3050 in your browser
- The application should load!

## Summary

**You need TWO servers running:**
1. ✅ API Server (port 8000) - **Already running!**
2. ❌ Web Server (port 3050) - **Start this now!**

Run `./START_WEB_SERVER.sh` in a new terminal window.
