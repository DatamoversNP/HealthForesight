# Fix All String Policy ID Endpoints

## Problem
Multiple API endpoints were returning 422 (Unprocessable Content) errors because they expected UUID policy IDs but were receiving string IDs like `PA_MRI_OP_001`.

## Endpoints Fixed ✅

### 1. Learning Accuracy Endpoints
- `GET /learning/accuracy/{policy_id}` - Now accepts both UUID and string IDs
- `GET /learning/accuracy/history/{policy_id}` - Now accepts both UUID and string IDs

### 2. Scenario Accuracy Endpoint
- `GET /scenario-accuracy?policy_id=...` - Now accepts string policy_id in query params

### 3. Observations Endpoint
- `GET /observations?policy_id=...` - Now accepts string policy_id in query params

### 4. Simulate Analysis Endpoint
- `POST /analyses/simulate` - `SimulateAnalysisCreate` model now accepts `policy_id: UUID | str`

## Implementation Details

All endpoints now:
1. Try to parse the policy_id as UUID first
2. If that fails, search all policies by string ID
3. Use the policy's actual ID (which might be UUID or string) for internal operations
4. Return results correctly regardless of ID format

## Next Steps

**Restart the API server:**
```bash
# Stop current server (CTRL+C)
./START_API_NOW.sh
```

**Then refresh your browser** - the 422 errors should be gone!

## Expected Results

After restarting, you should see:
- ✅ No more 422 errors for `/learning/accuracy/{policy_id}`
- ✅ No more 422 errors for `/scenario-accuracy?policy_id=...`
- ✅ No more 422 errors for `/observations?policy_id=...`
- ✅ No more 422 errors for `/analyses/simulate`

The 404 errors for predicted-impact are expected until you generate predicted impact (which should now work with the previous fixes).
