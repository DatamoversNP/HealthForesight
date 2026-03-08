# Start API Server

The frontend is loading but can't connect to the API because the API server is not running.

## Quick Fix

Open a **NEW terminal window** and run:

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729/apps/api/src
export PYTHONPATH="$(pwd)/../../..:$(pwd)/../../../packages/common/src:$PYTHONPATH"
python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload
```

## What to Expect

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

## Then Refresh Browser

Once the API starts, refresh your browser at http://localhost:3050 and the errors should go away!

## Keep Terminal Open

**Important**: Keep the terminal window open while using the application. The API server needs to keep running.

To stop the server, press `Ctrl+C` in the terminal.

## Current Status

- ✅ **Frontend**: Running on port 3050
- ❌ **API**: NOT running on port 8000 ← **Start this now!**

Once both are running, the application will work!
