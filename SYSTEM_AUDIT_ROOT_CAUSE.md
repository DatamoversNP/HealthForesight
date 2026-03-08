# SYSTEM AUDIT - ROOT CAUSE ANALYSIS

## STEP 1: SYSTEM AUDIT COMPLETE

### CRITICAL BUG IDENTIFIED: Metadata Overwrite in Policy Loading

**Location:** `apps/api/src/uepi_api/storage/policy_storage.py`, line 317

**Root Cause:**
The policy loading code merges policies from multiple sources in this order:
1. Storage adapter (Azure File Storage)
2. `/tmp/policies_{tenant_id}.json`
3. `data/policies_{tenant_id}.json`
4. `data/valid_policies.json`
5. **`apps/api/data/policies/policy-*.json`** ← LOADS WITH EMPTY METADATA
6. `data/policy_*.json` ← HAS METADATA BUT LOADS TOO LATE

**The Bug:**
At line 317, when loading from `apps/api/data/policies/` (step 5):
```python
existing['metadata'].update({k: v for k, v in policy['metadata'].items() if k != 'predicted_impact'})
```

If `apps/api/data/policies/policy-*.json` files have `{"metadata": {}}` (empty), this `.update()` call **overwrites** the metadata that was already loaded from `data/policy_*.json` files.

**Why This Happens:**
- `apps/api/data/policies/` files are loaded AFTER `data/policy_*.json` files
- But the merge logic at line 317 uses `.update()` which replaces values
- Empty metadata from `apps/api/data/policies/` overwrites non-empty metadata from `data/policy_*.json`

**Evidence from Logs:**
```
✅ Loaded 43 policy files from storage adapter
✅ Loaded 32 unique policies from storage adapter
DEBUG get_policy: Policy 46c9bfda-1678-4d91-8dcb-6aeaff5537db - has metadata: True, root assumptions: 0, metadata assumptions: 0, guardrails: 0, versions: 0
```

The policy is found, has metadata=True, but all counts are 0 because empty metadata overwrote the real metadata.

### Data Flow Analysis

**Policy Creation:**
- Policies created via API → stored in `apps/api/data/policies/policy-*.json`
- These files have minimal metadata (just `{"metadata": {}}`)

**Workspace Data (Assumptions, Guardrails, Versions):**
- Stored in `data/policy_*.json` files with full metadata
- OR stored in separate directories: `data/policy_assumptions/`, `data/policy_guardrails/`, etc.

**Loading Order (WRONG):**
1. Storage adapter loads `apps/api/data/policies/policy-*.json` (empty metadata)
2. Local files load `data/policy_*.json` (has metadata)
3. Merge happens: `apps/api/data/policies/` OVERWRITES `data/policy_*.json` metadata

**Expected Order (CORRECT):**
1. Load `data/policy_*.json` first (has metadata)
2. Load `apps/api/data/policies/` second
3. Merge: Only update metadata if source has MORE data, not less

### Additional Issues Found

1. **No QA Test Script Found**
   - User mentioned `./scripts/testing/run-qa-tests.sh` but it doesn't exist
   - Only found `scripts/test_baseline_predicted_observed.py` which tests API endpoints, not storage layer

2. **Metadata Merge Logic is Destructive**
   - Line 317: `.update()` replaces entire metadata dict
   - Should be: Deep merge that preserves existing non-empty values

3. **Deployment Script Issue**
   - `START_PRODUCTION_BUILD.sh` copies `apps/api/data/policies/` files
   - But these files on Azure still have empty metadata (not updated by merge script)

4. **Storage Path Confusion**
   - Multiple storage paths: `/tmp/`, `data/`, `apps/api/data/policies/`
   - No clear single source of truth
   - Merge logic tries to handle all but fails

### Required Fixes

1. **Fix Metadata Merge Logic** (CRITICAL)
   - Change line 317 to preserve existing metadata if new metadata is empty
   - Only update metadata fields that are actually present and non-empty

2. **Fix Loading Order** (CRITICAL)
   - Load `data/policy_*.json` AFTER `apps/api/data/policies/`
   - OR: Load `apps/api/data/policies/` first, then merge `data/policy_*.json` metadata into it

3. **Consolidate Storage**
   - Choose ONE location for policy files
   - Either all in `data/policy_*.json` OR all in `apps/api/data/policies/`
   - Not both

4. **Create QA Tests**
   - Test policy loading with metadata from multiple sources
   - Verify metadata is preserved correctly
   - Test merge logic with empty vs non-empty metadata

## NEXT STEPS

1. Fix the metadata merge logic in `policy_storage.py`
2. Test locally to verify metadata is preserved
3. Create QA test script to validate
4. Only then consider deployment

