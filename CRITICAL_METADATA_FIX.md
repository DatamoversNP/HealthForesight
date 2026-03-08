# Critical Metadata Fix - Root Cause Found

## Root Cause

The problem was in `get_policy()` and `list_policies()` in `storage_policies.py`:

**Before (BROKEN):**
```python
if key not in policy_dict and key in metadata:
    policy_dict[key] = metadata[key]
```

This only copies metadata to root level if the key is NOT already in policy_dict. But if an earlier source (like storage adapter) already set `assumptions: []` (empty list), then `key in policy_dict` is True, so it won't copy the metadata from the individual file!

**After (FIXED):**
```python
# Always copy workspace data from metadata - individual files are source of truth
for key in ['assumptions', 'guardrails', 'versions', 'changelog']:
    if key in metadata:
        policy_dict[key] = metadata[key]  # Always override, even if root has empty value
```

## What This Fixes

- ✅ Workspace data (assumptions, guardrails, versions) now ALWAYS comes from metadata
- ✅ Individual policy files (loaded last) now properly override earlier sources
- ✅ Even if earlier sources set empty lists, metadata from individual files takes precedence

## Files Fixed

1. `apps/api/src/uepi_api/storage_policies.py`
   - `get_policy()` - Fixed metadata copying
   - `list_policies()` - Fixed metadata copying

## Deploy Now

```bash
./COMPREHENSIVE_DATA_FIX.sh
```

This should finally fix the metadata loading issue!

