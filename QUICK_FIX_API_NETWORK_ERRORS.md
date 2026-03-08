# Quick Fix: API Network Errors

## 🔴 Problem
- ❌ API is NOT running → Network errors in frontend
- ❌ No data loading → API connection refused

## ✅ Solution: Start the API

### Method 1: Use the Script (Recommended)

**Open a terminal and run:**
```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
./start_api_local.sh
```

**Wait 15-20 seconds** for the API to start. You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Method 2: Manual Start (If script fails)

**Step 1: Set environment variables**
```bash
export PYTHONPATH="${PWD}/apps/api/src:${PWD}/packages/common/src:$PYTHONPATH"
export STORAGE_PATH="${PWD}/data"
```

**Step 2: Navigate to API directory**
```bash
cd apps/api
```

**Step 3: Activate virtual environment (if exists)**
```bash
source .venv/bin/activate  # or: source venv/bin/activate
```

**Step 4: Start the API**
```bash
cd ../..
python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🔍 Verify API is Running

**In another terminal, run:**
```bash
./diagnose_api_network.sh
```

**Or check manually:**
```bash
# Check if API is running
lsof -ti:8000

# Test health endpoint
curl http://localhost:8000/health

# Test policies endpoint
curl http://localhost:8000/api/v1/policies
```

## 📊 Check Logs

**View API logs:**
```bash
./view_logs.sh api
```

**View errors:**
```bash
./view_logs.sh error
```

**Search for network errors:**
```bash
./search_logs.sh "network\|connection\|refused"
```

## ⚠️ Common Issues

### Issue 1: Port 8000 Already in Use

**Fix:**
```bash
lsof -ti:8000 | xargs kill -9
./start_api_local.sh
```

### Issue 2: Import Errors

**Fix:**
```bash
export PYTHONPATH="${PWD}/apps/api/src:${PWD}/packages/common/src:$PYTHONPATH"
```

### Issue 3: Missing Dependencies

**Fix:**
```bash
cd apps/api
pip install -r requirements.txt
```

### Issue 4: STORAGE_PATH Not Set

**Fix:**
```bash
export STORAGE_PATH="${PWD}/data"
```

## ✅ After API Starts

Once you see "Application startup complete":
1. ✅ Network errors will stop
2. ✅ Data will start loading
3. ✅ Frontend will connect
4. ✅ Logs will be generated

## 🚀 Quick Commands

**Start API:**
```bash
./start_api_local.sh
```

**Check Status:**
```bash
./diagnose_api_network.sh
```

**View Logs:**
```bash
./view_logs.sh api
```

**Start Web (if needed):**
```bash
./START_WEB_SERVER.sh
```

## 📋 Summary

**The API must be running for the frontend to work!**

1. Start API: `./start_api_local.sh`
2. Wait 15 seconds
3. Check status: `./diagnose_api_network.sh`
4. Open frontend: http://localhost:3050

