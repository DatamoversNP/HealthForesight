# Fixed Start Instructions - Complete Solution

## Issue
Python couldn't find both `uepi_api` and `uepi_common` modules because the Python path wasn't set correctly.

## Solution
Set the `PYTHONPATH` environment variable to include both:
- `apps/api/src` (for uepi_api)
- `packages/common/src` (for uepi_common)

## Correct Commands

### Option 1: Using the fixed start script (Easiest)
```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
./START_API_SERVER.sh
```

### Option 2: Manual with PYTHONPATH (from project root)
```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
export PYTHONPATH="$(pwd)/apps/api/src:$(pwd)/packages/common/src:${PYTHONPATH}"
cd apps/api
python3 -m uvicorn uepi_api.main:app --reload --port 8000
```

### Option 3: One-liner
```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729/apps/api && PYTHONPATH="../../apps/api/src:../../packages/common/src" python3 -m uvicorn uepi_api.main:app --reload --port 8000
```

### Option 4: Using the API start script
```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729/apps/api
./start.sh
```

## Start Frontend (Terminal 2)
```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729/apps/web
npm run dev
```

## Verify API is Running
```bash
# Check if server is responding
curl http://localhost:8000/docs
# Should show Swagger UI HTML

# Test API endpoint
curl http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer dev-token-123"
# Should return JSON with user info
```

## Access Points
- **Application**: http://localhost:3050
- **API Docs**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/api/v1/auth/me

## What Was Fixed

The start scripts now include both paths:
- `apps/api/src` - for the `uepi_api` module
- `packages/common/src` - for the `uepi_common` module

This ensures all imports work correctly.
