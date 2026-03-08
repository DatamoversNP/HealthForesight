# API Network Errors - Root Cause & Fix

## 🔍 Problem Identified

**Root Cause**: The API server is **NOT running** on port 8000.

This is why you're seeing:
- ❌ Network errors in the frontend
- ❌ No data loading
- ❌ API connection refused errors

## ✅ Solution

### Step 1: Start the API Server

**In a terminal, run:**
```bash
./start_api_local.sh
```

**Wait 10-15 seconds** for the API to start. You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Step 2: Verify API is Running

**In another terminal, run:**
```bash
./diagnose_api_network.sh
```

This will check:
- ✅ API is running
- ✅ Health endpoint responds
- ✅ Policies endpoint works
- ✅ Data files are accessible
- ✅ Web server status

### Step 3: Check Logs

**View API logs:**
```bash
./view_logs.sh api
```

**View errors:**
```bash
./view_logs.sh error
```

**Search for specific errors:**
```bash
./search_logs.sh "network\|error\|failed"
```

## 🔧 Troubleshooting

### If API Won't Start

**Check for port conflicts:**
```bash
lsof -ti:8000 | xargs kill -9
```

**Then start again:**
```bash
./start_api_local.sh
```

### If You See Import Errors

**Make sure PYTHONPATH is set:**
```bash
export PYTHONPATH="${PWD}/apps/api/src:${PWD}/packages/common/src:$PYTHONPATH"
export STORAGE_PATH="${PWD}/data"
```

### If Data Not Loading

**Check STORAGE_PATH:**
```bash
echo $STORAGE_PATH
ls -la $STORAGE_PATH/policies/ | head -5
```

**Should show policy JSON files.**

## 📋 Current Status

- ❌ **API Server**: NOT running (needs to be started)
- ❌ **Web Server**: Check with `lsof -ti:3050`
- ❌ **Data Loading**: Can't load because API is down

## 🚀 Quick Fix Commands

**Terminal 1 - Start API:**
```bash
./start_api_local.sh
```

**Terminal 2 - Start Web (if needed):**
```bash
./START_WEB_SERVER.sh
```

**Terminal 3 - Check Status:**
```bash
./diagnose_api_network.sh
```

## ✅ After Starting API

Once the API is running:
1. ✅ Network errors will stop
2. ✅ Data will start loading
3. ✅ Frontend will connect successfully
4. ✅ Logs will be generated in `logs/` directory

## 📊 Monitor Logs

**Watch API logs in real-time:**
```bash
./view_logs.sh api
```

**Watch errors:**
```bash
./view_logs.sh error
```

**Search for network errors:**
```bash
./search_logs.sh "network\|connection\|refused"
```

## 💡 Next Steps

1. **Start the API**: `./start_api_local.sh`
2. **Wait 15 seconds** for startup
3. **Run diagnostics**: `./diagnose_api_network.sh`
4. **Check the frontend**: http://localhost:3050
5. **Monitor logs**: `./view_logs.sh api`

The API must be running for the frontend to work!

