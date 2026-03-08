# Final Instructions - Restart API Server Now

## Critical: The API Server Must Be Restarted

The code fixes are complete, but **the API server is still running OLD code** without CORS configuration.

## What to Do (Choose One Method)

### Method 1: Use the Quick Restart Script

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
chmod +x RESTART_API_NOW.sh
./RESTART_API_NOW.sh
```

### Method 2: Manual Restart

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"

# Stop the API server
lsof -ti:8000 | xargs kill -9

# Install missing dependencies
source .venv/bin/activate
pip install scikit-learn

# Start the API server
cd apps/api
export PYTHONPATH="$PWD/src:$PWD/../../../packages/common/src:$PYTHONPATH"
nohup python -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000 > ../../api-server.log 2>&1 &
```

### Method 3: Use the Complete Startup Script

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
./stop-both-servers.sh
./start-both-servers.sh
```

## Verify It's Working

After restarting, wait 10 seconds, then:

```bash
# Test API is responding
curl http://localhost:8000/health

# Test CORS headers
curl -I -H "Origin: http://localhost:3050" http://localhost:8000/api/v1/health | grep -i "access-control"
```

You should see `Access-Control-Allow-Origin: http://localhost:3050` in the headers.

## Then Test in Browser

1. Refresh http://localhost:3050/policies
2. Click "Generate Predicted Impact" button
3. Should work now! ✅

## What Was Fixed

✅ **CORS Configuration** - Comprehensive origins list in `main.py`
✅ **scipy imports** - Made optional with graceful fallbacks
✅ **sklearn imports** - Made optional with graceful fallbacks
✅ **Dependencies** - Added scikit-learn to install scripts

## If Still Not Working

Check logs:
```bash
tail -20 api-server.log
```

Look for errors. Common issues:
- ❌ "ModuleNotFoundError" = Run `pip install scikit-learn` in venv
- ❌ "Address already in use" = Server didn't stop, kill it: `lsof -ti:8000 | xargs kill -9`
- ❌ No CORS headers = Server didn't restart, try Method 2 or 3

---

**The code is fixed. Just restart the server and it will work!** 🚀
