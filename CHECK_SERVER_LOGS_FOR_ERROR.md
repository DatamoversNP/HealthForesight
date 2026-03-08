# How to Check Server Logs for Baseline Analysis Error

## Current Issue
Error message is truncated: "Missing dependency: cann..." - we need to see the full error.

## Step 1: Check API Server Logs

The API server logs should show the full error. Check:

```bash
# View recent logs
tail -100 api-server.log | grep -A 10 -i "error\|exception\|traceback\|baseline"

# Or view live logs while running baseline analysis
tail -f api-server.log
```

## Step 2: Verify Server Was Restarted

The changes I made won't take effect until the server is restarted:

```bash
# Stop servers
./stop-both-servers.sh

# Start servers (this installs statsmodels if missing)
./start-both-servers.sh
```

## Step 3: Check What's Actually Missing

The error might be:
1. `statsmodels` not installed
2. `scipy` not installed  
3. `scikit-learn` not installed
4. Some other dependency

## Step 4: Install Dependencies Manually (if needed)

If dependencies are missing in the venv:

```bash
# Activate venv
source .venv/bin/activate

# Install dependencies
pip install scipy scikit-learn statsmodels

# Verify installation
python3 -c "import scipy; import sklearn; import statsmodels; print('✅ All dependencies available')"
```

## Step 5: Better Error Message

After restarting, the endpoint will now:
- Check dependencies upfront
- Try to import BaselineAnalysisEngine and catch import errors
- Provide clear error messages

If you see a 503 error (not 500), that means the new code is running and will tell you exactly what's missing.

## Alternative: Check via Python

You can check dependencies directly:

```bash
source .venv/bin/activate
python3 <<EOF
try:
    import scipy
    print("✅ scipy available")
except ImportError as e:
    print(f"❌ scipy missing: {e}")

try:
    import sklearn
    print("✅ scikit-learn available")
except ImportError as e:
    print(f"❌ scikit-learn missing: {e}")

try:
    import statsmodels
    print("✅ statsmodels available")
except ImportError as e:
    print(f"❌ statsmodels missing: {e}")

try:
    from uepi_common.analytics.baseline import BaselineAnalysisEngine
    print("✅ BaselineAnalysisEngine import successful")
except ImportError as e:
    print(f"❌ BaselineAnalysisEngine import failed: {e}")
EOF
```

This will show exactly what's missing!
