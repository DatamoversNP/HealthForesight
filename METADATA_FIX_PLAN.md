# Policy Metadata Not Loading on Azure - Fix Plan

## Problem Summary

- ✅ **Predicted impacts ARE loading** on Azure (working correctly)
- ❌ **Policy metadata (assumptions, guardrails, versions) NOT loading** on Azure
- ✅ **Works correctly locally** - metadata is present in local policy files

## Root Cause Analysis

The metadata (assumptions, guardrails, versions) is stored in the `metadata` field of policy JSON files. The code tries to:
1. Load policies from multiple sources (storage adapter, local files)
2. Merge metadata from different sources
3. Copy metadata fields to root level for easier access

**The issue is likely:**
- Policy files on Azure don't have metadata embedded, OR
- Metadata merge logic is not working correctly on Azure, OR
- Policies are being loaded from a source that doesn't have metadata

## Diagnostic Steps

### Step 1: Run Diagnostic Script

```bash
./diagnose_metadata_issue.sh
```

This will check:
- What the workspace endpoint returns
- What the individual policy endpoint returns
- Whether metadata exists in responses
- Whether assumptions/guardrails/versions endpoints work

### Step 2: Run Comprehensive Validation

```bash
./validate_all_endpoints.sh
```

This will test ALL endpoints and functionalities to identify what's working and what's not.

## Fix Strategy

### Option 1: Verify Policy Files Have Metadata (Most Likely Issue)

The policy files in `data/policy_*.json` should have a `metadata` field with `assumptions`, `guardrails`, and `versions`. 

**Check locally:**
```bash
# Check if a policy file has metadata
cat data/policy_ST_BIOLOGIC_006.json | python3 -c "import sys, json; data=json.load(sys.stdin); print('Has metadata:', 'metadata' in data); print('Metadata keys:', list(data.get('metadata', {}).keys()) if 'metadata' in data else 'None'); print('Assumptions:', len(data.get('metadata', {}).get('assumptions', []))); print('Guardrails:', len(data.get('metadata', {}).get('guardrails', []))); print('Versions:', len(data.get('metadata', {}).get('versions', [])))"
```

**If metadata is missing from policy files:**
- The metadata might be in separate files in `data/policy_assumptions/`, `data/policy_guardrails/`, `data/policy_versions/`
- We need to merge this data into the policy files before deployment

### Option 2: Ensure Metadata is Preserved During Deployment

The `COMPREHENSIVE_DATA_FIX.sh` script already copies all data files. But we need to verify:
1. Policy files with metadata are included
2. The API can read them correctly on Azure

### Option 3: Fix Metadata Loading Logic

The `_load_from_file` method in `policy_storage.py` has logic to merge metadata, but it might not be working correctly on Azure. We may need to:
1. Ensure metadata from local files takes precedence
2. Fix the merge logic to preserve all metadata fields

## Immediate Actions

1. **Run diagnostics:**
   ```bash
   ./diagnose_metadata_issue.sh
   ./validate_all_endpoints.sh
   ```

2. **Check local policy files:**
   ```bash
   # Check if policy files have metadata
   for file in data/policy_*.json; do
     echo "Checking $file..."
     python3 -c "import sys, json; data=json.load(open('$file')); print(f\"  Has metadata: {'metadata' in data}, Assumptions: {len(data.get('metadata', {}).get('assumptions', []))}, Guardrails: {len(data.get('metadata', {}).get('guardrails', []))}, Versions: {len(data.get('metadata', {}).get('versions', []))}\")"
   done
   ```

3. **If metadata is in separate files, merge them:**
   - We have a script `apps/api/scripts/migrate_workspace_data_to_policies.py` that should do this
   - Run it to embed metadata into policy files

4. **Deploy with all data:**
   ```bash
   ./COMPREHENSIVE_DATA_FIX.sh
   ```

5. **Verify after deployment:**
   ```bash
   ./diagnose_metadata_issue.sh
   ./validate_all_endpoints.sh
   ```

## Expected Results After Fix

- ✅ Policy workspace endpoint returns assumptions, guardrails, versions
- ✅ Individual assumptions/guardrails/versions endpoints work
- ✅ All policy workspace tabs load data on frontend
- ✅ Decisions, risks, comments, activity, narratives link correctly to policies

## Files to Check/Modify

1. `apps/api/src/uepi_api/storage/policy_storage.py` - Metadata merge logic
2. `apps/api/src/uepi_api/storage_policies.py` - `get_policy()` metadata extraction
3. `data/policy_*.json` - Policy files should have `metadata` field
4. `COMPREHENSIVE_DATA_FIX.sh` - Deployment script (already includes all data)

