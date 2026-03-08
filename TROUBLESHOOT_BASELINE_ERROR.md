# Troubleshooting Baseline Analysis Error

## Current Error
```
500 Internal Server Error
"Baseline analysis failed: Missing dependency: cann..."
```

The error message is truncated. We need to see the full error.

## Solution Steps

### Step 1: Check Dependencies

Run the diagnostic script I created:

```bash
python3 scripts/check_baseline_dependencies.py
```

This will show exactly what's missing.

### Step 2: Check Server Logs

The API server logs have the full error message:

```bash
# View recent error logs
tail -100 api-server.log | grep -A 20 -i "error\|exception\|traceback\|baseline\|dependency"

# Or watch logs in real-time
tail -f api-server.log
```

### Step 3: Restart Server with Dependencies

The server needs to be restarted to:
1. Pick up my code changes (better error messages)
2. Install missing dependencies (if using startup script)

```bash
# Stop servers
./stop-both-servers.sh

# Start servers (will install statsmodels if missing)
./start-both-servers.sh
```

### Step 4: Install Dependencies Manually (if needed)

If dependencies are still missing after restart:

```bash
# Activate the venv (if using one)
source .venv/bin/activate

# Install all baseline dependencies
pip install scipy scikit-learn statsmodels pandas numpy

# Verify
python3 scripts/check_baseline_dependencies.py
```

### Step 5: Check Import Path

The error might also be a Python path issue. Verify the module can be imported:

```bash
source .venv/bin/activate
python3 <<EOF
import sys
sys.path.insert(0, 'apps/api/src')
sys.path.insert(0, 'packages/common/src')

try:
    from uepi_common.analytics.baseline import BaselineAnalysisEngine
    print("✅ Import successful!")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
EOF
```

## What I Changed

1. **Added dependency check** at start of endpoint (returns 503 with clear message)
2. **Added statsmodels** to startup script
3. **Improved error handling** to catch import errors from BaselineAnalysisEngine

## Expected Behavior After Fix

**Before restart:**
- 500 error with truncated message

**After restart:**
- 503 error with clear message: "Missing required dependencies: scipy, scikit-learn, statsmodels. Please install them: pip install scipy scikit-learn statsmodels"
- OR baseline analysis works if all dependencies are present

## Quick Diagnostic

Run this to see what's missing:
```bash
source .venv/bin/activate  # if using venv
python3 scripts/check_baseline_dependencies.py
```

This will tell you exactly what needs to be installed!
