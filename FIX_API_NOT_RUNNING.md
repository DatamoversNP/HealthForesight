# Fix: API Server Not Running

## Problem

You're seeing these errors:
- `GET http://localhost:8000/api/v1/me net::ERR_CONNECTION_TIMED_OUT`
- `Network error: Network Error`
- `API unavailable, using mock user`

This means: **The API server is NOT running on port 8000**

## Solution

### Quick Fix: Start API Server

**From project root, run:**

```bash
./START_PLATFORM_COMPLETE.sh
```

This will:
1. ✅ Ensure index.html points to main platform (not marketing)
2. ✅ Stop any existing servers
3. ✅ Start API server on port 8000
4. ✅ Start Web server on port 3050
5. ✅ Verify both are running

### Or Start API Server Separately

**Terminal 1 - API Server:**

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
./START_API_SERVER.sh
```

**Terminal 2 - Web Server (if not already running):**

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution/apps/web"
npm run dev
```

## Verify API is Running

```bash
# Check if API server is running
curl http://localhost:8000/health

# Or check port
lsof -i:8000

# Should show process listening on port 8000
```

## What Should Happen

1. **API Server starts** → http://localhost:8000/health should respond
2. **Web Server connects** → No more "Network Error" messages
3. **Platform works** → Login, dashboard, etc. all functional

## Current Status

- ✅ **index.html fixed** → Now loads main platform (`main.tsx`)
- ❌ **API server NOT running** → Need to start it on port 8000
- ✅ **Web server running** → Port 3050 is working

## After Starting API

Once the API server is running:
- ✅ No more "Network Error" messages
- ✅ API calls will work
- ✅ Login will work
- ✅ Dashboard will load data
- ✅ All features will be functional

## Quick Command (Copy & Paste)

From project root:

```bash
./START_PLATFORM_COMPLETE.sh
```

This starts everything correctly!
