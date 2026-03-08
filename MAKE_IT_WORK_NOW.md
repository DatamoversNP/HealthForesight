# MAKE IT WORK NOW - Simple Steps

## The Problem
- Server needs to be running
- Need to create observations for all policies

## Solution (2 Steps)

### Step 1: Start API Server
**In a terminal, run:**
```bash
cd apps/api/src
export PYTHONPATH="$(pwd)/../../..:$(pwd)/../../../packages/common/src:$PYTHONPATH"
python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Wait until you see:** `Application startup complete`

### Step 2: Create Observations
**In another terminal, run:**
```bash
cd apps/api
python3 scripts/create_observations_simple.py
```

This will:
- ✅ Get all policies
- ✅ For each policy, call `/observations/from-analysis/{id}`
- ✅ That endpoint auto-completes PENDING analyses
- ✅ Then creates observations
- ✅ Shows you results

## That's It!

After Step 2 completes, refresh your web page - all observations will be visible!
