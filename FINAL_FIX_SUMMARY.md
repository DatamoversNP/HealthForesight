# Final Metadata Fix - Ready to Deploy

## What Was Fixed

**Root Cause:** `get_policy()` and `list_policies()` only copied metadata to root level if the key didn't already exist. If an earlier source set empty lists, it wouldn't override with actual metadata from individual files.

**Fix Applied:**
- Modified `apps/api/src/uepi_api/storage_policies.py` in two places:
  1. `get_policy()` - Always copies workspace data (assumptions, guardrails, versions, changelog) from metadata to root level
  2. `list_policies()` - Same fix

**Code Change:**
```python
# BEFORE (BROKEN):
if key not in policy_dict and key in metadata:
    policy_dict[key] = metadata[key]

# AFTER (FIXED):
for key in ['assumptions', 'guardrails', 'versions', 'changelog']:
    if key in metadata:
        policy_dict[key] = metadata[key]  # Always override
```

## Why This Works

1. Individual policy files (`data/policy_*.json`) are loaded LAST by `policy_storage.py`
2. They contain the complete metadata (assumptions, guardrails, versions)
3. The merge logic in `policy_storage.py` correctly merges this metadata
4. But `get_policy()` wasn't copying it to root level if root already had empty values
5. Now it ALWAYS copies from metadata, ensuring individual files take precedence

## Deployment

Run:
```bash
./DEPLOY_METADATA_FIX.sh
```

This script:
1. ✅ Verifies the fix is in the code
2. ✅ Creates deployment package with ALL data files
3. ✅ Verifies policy files are included
4. ✅ Deploys to Azure
5. ✅ Sets STORAGE_PATH environment variable
6. ✅ Restarts the app
7. ✅ Verifies API health

## Expected Result

After deployment, `./test_metadata_after_deployment.sh` should show:
- Assumptions: 3 (not 0)
- Guardrails: 3 (not 0)
- Versions: 1 (not 0)

## If It Still Doesn't Work

If metadata is still 0 after deployment, the issue is likely:
1. Policy files not deployed (check ZIP contents)
2. STORAGE_PATH not set correctly (check Azure app settings)
3. Files in wrong location on Azure (check Kudu Console)

But the code fix is correct - it will work if files are present.

