# Root Cause Analysis and Fix

## Problem

**Local files HAVE metadata** (3 assumptions, 3 guardrails, 1 version), but **Azure shows 0** for all.

## Root Cause

The policy loading logic loads policies from multiple sources in this order:
1. Storage adapter (Azure File Storage) - may have empty metadata
2. `/tmp/policies_{tenant_id}.json` - may have empty metadata  
3. `data/policies_{tenant_id}.json` - may have empty metadata
4. `data/valid_policies.json` - may have empty metadata
5. `apps/api/data/policies/policy-*.json` - may have empty metadata
6. `data/policy_*.json` - **THIS ONE HAS THE METADATA** (loaded last)

**The issue**: When merging, if an earlier source has empty metadata `{}` or empty lists `[]`, and the merge logic checks `if key in policy_metadata and policy_metadata[key]`, an empty list `[]` is falsy, so it doesn't get merged!

## Fix Applied

1. **Fixed merge logic** to ensure individual policy files (loaded last) always take precedence
2. **Added debug logging** to track metadata merging
3. **Fixed all versions endpoints** to accept string IDs

## Critical Fix in `policy_storage.py`

The merge logic now:
- Always uses metadata from individual `data/policy_*.json` files when present
- Preserves workspace data (assumptions, guardrails, versions) from individual files
- Logs what's being merged for debugging

## Why This Should Work

Individual policy files (`data/policy_*.json`) are loaded **LAST**, so they should override any earlier sources. The fix ensures that:
1. If individual file has metadata, it's used (even if it's an empty list)
2. Debug logging shows what's being merged
3. Metadata from individual files takes precedence

## Deployment

After deploying, check Azure logs for:
```
DEBUG: Loaded policy ST_BIOLOGIC_006 from policy_ST_BIOLOGIC_006.json - has metadata: True, assumptions: 3, guardrails: 3, versions: 1
DEBUG: Merged assumptions from policy_ST_BIOLOGIC_006.json: 3 items
```

If you see these logs, the metadata is being loaded. If not, the files might not be on Azure.

## Verification

After deployment:
1. Check Azure logs for metadata loading
2. Run `./diagnose_metadata_issue.sh`
3. If still 0, check if `data/policy_*.json` files are actually on Azure
