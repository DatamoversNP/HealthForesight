# Fix String Policy ID Support

## Problem
The API was returning 422 (Unprocessable Content) errors when the frontend tried to fetch predicted impact for policies with string IDs like `PA_MRI_OP_001`, `SOC_INFUSION_002`, etc.

The API endpoints were expecting UUIDs only, but the preconfigured policies use string IDs.

## Fixes Applied ✅

### 1. Updated Policy Endpoints
All policy endpoints now accept both UUID and string IDs:

- `GET /policies/{policy_id}` - Get policy by ID
- `GET /policies/{policy_id}/predicted-impact` - Get predicted impact
- `POST /policies/{policy_id}/predicted-impact` - Generate predicted impact
- `POST /policies/{policy_id}/refresh-prediction` - Refresh stale prediction
- `PUT /policies/{policy_id}` - Update policy
- `DELETE /policies/{policy_id}` - Delete policy

### 2. Updated Storage Functions
- `get_policy()` in `storage_policies.py` now handles both UUID and string IDs
- `get_predicted_impact()` in `storage_policy_predicted_impact.py` now handles both UUID and string IDs
- `get_policy()` in `policy_storage.py` already handled both (updated earlier)

### 3. ID Resolution Logic
The code now:
1. First tries to parse the ID as a UUID
2. If that fails, searches all policies by string ID
3. Returns the matching policy regardless of ID format

## Next Steps

**Restart the API server:**
```bash
# Stop current server (CTRL+C)
./START_API_NOW.sh
```

**Then refresh your browser** - the 422 errors should be gone!

The frontend should now be able to:
- ✅ Load policies with string IDs
- ✅ Fetch predicted impact for policies with string IDs
- ✅ Generate predicted impact for policies with string IDs

## Verification

After restarting, check the browser console - you should no longer see:
```
GET http://localhost:8000/api/v1/policies/PA_MRI_OP_001/predicted-impact 422 (Unprocessable Content)
```

Instead, you should see either:
- 200 OK (if predicted impact exists)
- 404 Not Found (if predicted impact doesn't exist yet - this is expected and you can generate it)
