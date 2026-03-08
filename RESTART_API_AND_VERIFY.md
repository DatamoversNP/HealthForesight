# Restart API Server to Fix Predicted Impact Loading

## Issue
The API server is still using the old policy loading logic that doesn't merge predicted_impact from `apps/api/data/policies/`. The new merge logic needs a server restart to take effect.

## Solution

**Restart the API server:**

1. **Stop the current server:**
   - Find the terminal running the API
   - Press `CTRL+C` to stop it

2. **Start it again:**
   ```bash
   ./START_API_NOW.sh
   ```

3. **Wait for it to start** (you should see "Uvicorn running on http://0.0.0.0:8000")

4. **Refresh your browser** - the 404 errors should be gone!

## What Changed

The new loading logic:
- ✅ Loads policies from ALL sources (valid_policies.json, apps/api/data/policies/, etc.)
- ✅ Merges them by policy_id
- ✅ Prioritizes predicted_impact from apps/api/data/policies/ (where it was saved)
- ✅ Returns complete policies with predicted_impact

## Verification

After restarting, you can verify it's working:

```bash
curl http://localhost:8000/api/v1/policies/PA_MRI_OP_001/predicted-impact
```

Should return predicted impact data (not 404).

## Expected Results

After restart:
- ✅ No more 404 errors
- ✅ Predicted impact visible in UI
- ✅ All 5 policies show their predicted impact metrics
