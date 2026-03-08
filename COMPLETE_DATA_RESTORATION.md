# Complete Data Restoration Guide

## Problem
All existing data (policies, baselines, observations, analyses, pipeline runs, etc.) was not loading in the local application.

## Root Causes Fixed

### 1. Storage Path Issue (FIXED ✅)
- **Problem**: Code was trying to use `/home/data` which doesn't work on macOS
- **Fix**: Updated `storage_file.py` to detect macOS and use `./data` instead
- **File**: `apps/api/src/uepi_api/storage_file.py`

### 2. Policy Storage Location (FIXED ✅)
- **Problem**: Policies were in `data/valid_policies.json` but API looked in `/tmp/policies_{tenant_id}.json`
- **Fix**: Updated `policy_storage.py` to check multiple locations:
  - `/tmp/policies_{tenant_id}.json`
  - `data/policies_{tenant_id}.json`
  - `data/valid_policies.json`
  - Individual `data/policy_*.json` files
- **File**: `apps/api/src/uepi_api/storage/policy_storage.py`

### 3. Pipeline Storage Paths (FIXED ✅)
- **Problem**: Pipelines and pipeline runs calculated their own BASE_PATH
- **Fix**: Updated to use the same BASE_PATH from `storage_file.py`
- **Files**: 
  - `apps/api/src/uepi_api/storage_pipelines.py`
  - `apps/api/src/uepi_api/storage_pipeline_runs.py`

### 4. FileStorage Index Issue (FIXED ✅)
- **Problem**: FileStorage only read from `index.json`, so existing files weren't found if index was empty
- **Fix**: Updated `FileStorage.list_all()` to scan directory for existing files if index is empty
- **File**: `packages/common/src/uepi_common/storage/file_storage.py`

## How to Restore Your Data

### Quick Method (Recommended)

1. **Restart the API server:**
   ```bash
   # Stop current server (CTRL+C)
   ./START_API_NOW.sh
   ```

2. **Refresh your browser** at http://localhost:3050

The code now automatically finds your existing data in the `data/` directory!

### Comprehensive Method (If Quick Method Doesn't Work)

1. **Run the restoration script:**
   ```bash
   ./RESTORE_ALL_DATA.sh
   ```

2. **Restart the API server:**
   ```bash
   ./START_API_NOW.sh
   ```

3. **Refresh your browser**

## What Data Will Be Restored

All data in your `data/` directory will be automatically found:

- ✅ **Policies**: From `data/valid_policies.json` and `data/policy_*.json`
- ✅ **Baselines**: From `data/baselines/{tenant_id}/*.json`
- ✅ **Observations**: From `data/observations/{tenant_id}/*.json`
- ✅ **Analyses**: From `data/analyses/*.json`
- ✅ **Pipelines**: From `data/pipelines/*.json`
- ✅ **Pipeline Runs**: From `data/pipeline_runs/*.json`
- ✅ **Scorecards**: From `data/scorecards/{tenant_id}/*.json`
- ✅ **All other data**: Automatically discovered

## Verification

After restarting, check:

1. **Policies**: http://localhost:3050/policies
2. **Analyses**: http://localhost:3050/analyses
3. **Baselines**: http://localhost:3050/baseline-analysis
4. **Observations**: http://localhost:3050/observation-analysis
5. **Pipelines**: http://localhost:3050/pipelines
6. **Pipeline Monitoring**: http://localhost:3050/pipeline-monitoring

## Technical Details

### Storage Path Resolution
The application now uses this logic:
1. Check `STORAGE_PATH` environment variable
2. If macOS (Darwin) or `/home` not writable → use `./data`
3. If Linux and `/home` writable → use `/home/data`
4. Default → use `./data`

### File Discovery
- **FileStorage** now scans directories if `index.json` is empty
- All storage modules use the same `BASE_PATH` from `storage_file.py`
- Policies are checked in multiple locations for maximum compatibility

## Troubleshooting

### Still Not Seeing Data?

1. **Check API logs** for messages like:
   ```
   ✅ Loaded policies from valid_policies.json
   ✅ Loaded X analyses
   ```

2. **Verify data exists:**
   ```bash
   ls -la data/policies/
   ls -la data/analyses/
   ls -la data/baselines/
   ```

3. **Check tenant ID**: Default is `00000000-0000-0000-0000-000000000001`
   - Make sure your data files have the correct `tenant_id` field

4. **Manual index rebuild**: If needed, delete empty index files:
   ```bash
   rm data/policies/index.json  # Will be rebuilt automatically
   rm data/pipelines/index.json
   ```

## Summary

✅ **Storage path fixed** - Uses `./data` on macOS  
✅ **Policy discovery fixed** - Checks multiple locations  
✅ **Pipeline paths fixed** - All use same BASE_PATH  
✅ **File discovery fixed** - Scans directories if index empty  
✅ **All data types supported** - Policies, baselines, observations, analyses, pipelines, etc.

**Your application should now show all existing data!**
