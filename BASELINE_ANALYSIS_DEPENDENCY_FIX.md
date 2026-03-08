# Baseline Analysis Dependency Fix

## Issue
Baseline analysis was failing with a 500 error: "Missing dependency: cann...lease ensure all required packages are installed."

## Root Cause
The `BaselineAnalysisEngine` requires optional dependencies:
- `scipy` - For statistical functions
- `scikit-learn` - For provider clustering (KMeans)
- `statsmodels` - For time series decomposition (STL)

These are imported conditionally in the baseline.py file, but the error wasn't being caught early enough.

## Fix Applied
Added dependency check at the beginning of `create_baseline_analysis` endpoint:
- Checks for `scipy`, `scikit-learn`, and `statsmodels` before running analysis
- Provides clear error message if any are missing
- Returns 503 (Service Unavailable) with installation instructions

## Solution
**The dependencies need to be installed in the API server environment.**

### If using venv:
```bash
source .venv/bin/activate
pip install scipy scikit-learn statsmodels
```

### If using start-both-servers.sh:
The script should install these, but verify they're in the requirements or add them to the install command in `start-both-servers.sh`.

### Quick Install Command:
```bash
pip install scipy scikit-learn statsmodels
```

## Next Steps

1. **Restart API Server** (to pick up the dependency check code):
   ```bash
   ./stop-both-servers.sh
   ./start-both-servers.sh
   ```

2. **Verify Dependencies** (in the API server environment):
   ```bash
   # If using venv
   source .venv/bin/activate
   python3 -c "import scipy; import sklearn; import statsmodels; print('✅ All dependencies available')"
   ```

3. **Run Baseline Analysis Again**:
   - Via UI: `http://localhost:3050/baseline-analysis`
   - Or via API: `POST /api/v1/analyses/baseline`

## Expected Behavior

**Before Fix:**
- Generic 500 error with truncated message
- Hard to diagnose missing dependencies

**After Fix:**
- Clear 503 error: "Missing required dependencies: scipy, scikit-learn, statsmodels. Please install them: pip install scipy scikit-learn statsmodels"
- Easy to identify and fix the issue

## Note
The baseline analysis code already handles missing dependencies gracefully (skips clustering if sklearn is missing, uses simple trend if statsmodels is missing), but having all dependencies ensures full functionality.
