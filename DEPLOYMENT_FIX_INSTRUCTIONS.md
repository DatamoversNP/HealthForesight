# Comprehensive Data Deployment Fix - Instructions

## Problem Summary

The Azure deployment is missing data, causing:
- ❌ Policy details (assumptions, guardrails, versions) not loading
- ❌ Predicted impact returning 404 errors
- ❌ Pipeline data not loading
- ❌ Observations, baselines, scenarios not loading
- ❌ API timeouts (30s exceeded)

## Root Cause

1. **Data files not deployed**: The deployment ZIP was excluding data directories
2. **API not finding data**: `STORAGE_PATH` not correctly set on Azure
3. **Predicted impact lookup inefficient**: Endpoint was loading all policies on every request

## Fixes Applied

### 1. Optimized Predicted Impact Endpoint ✅
- **File**: `apps/api/src/uepi_api/routers/policies_file.py`
- **Changes**:
  - Try UUID lookup first (faster, avoids loading all policies)
  - Fallback to string ID search only if UUID fails
  - Added fallback to check separate predicted impact files in `data/predicted_impacts/`
  - This reduces API response time and prevents timeouts

### 2. Comprehensive Data Deployment Script ✅
- **File**: `COMPREHENSIVE_DATA_FIX.sh`
- **What it does**:
  - Verifies all local data directories exist
  - Creates deployment package with **ALL** data directories:
    - `data/policies/`
    - `data/predicted_impacts/`
    - `data/observations/`
    - `data/baselines/`
    - `data/analyses/`
    - `data/analysis_results/`
    - `data/pipelines/`
    - `data/pipeline_runs/`
    - `data/scenarios/`
    - `data/decisions/`
    - `data/risks/`
    - `data/source_data/`
  - Deploys to Azure App Service
  - Sets `STORAGE_PATH="/home/site/wwwroot/data"` environment variable
  - Verifies deployment

## Deployment Steps

### Step 1: Run the Comprehensive Data Fix Script

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
chmod +x COMPREHENSIVE_DATA_FIX.sh
./COMPREHENSIVE_DATA_FIX.sh
```

This script will:
1. ✅ Verify all local data directories
2. ✅ Create deployment package with ALL data
3. ✅ Deploy to Azure App Service
4. ✅ Set `STORAGE_PATH` environment variable
5. ✅ Wait for deployment to complete
6. ✅ Verify API health

**Expected output:**
- Shows count of files in each data directory
- Creates ZIP package (may be large if data is extensive)
- Deploys to Azure
- Confirms API is healthy

### Step 2: Wait for Deployment

After the script completes:
- Wait **2-3 minutes** for Azure to fully process the deployment
- The API may restart during this time

### Step 3: Verify Deployment

#### Check API Health
```bash
curl https://healthforesight-api-9016.azurewebsites.net/health
```
Expected: `{"status":"healthy","service":"uepi-api"}`

#### Check Policies Endpoint
```bash
curl https://healthforesight-api-9016.azurewebsites.net/api/v1/policies | jq '. | length'
```
Expected: Should return a number > 0 (number of policies)

#### Check Predicted Impact (for a specific policy)
```bash
curl https://healthforesight-api-9016.azurewebsites.net/api/v1/policies/ST_BIOLOGIC_006/predicted-impact
```
Expected: Either predicted impact data or `{"detail":"Predicted impact not found for this policy"}` (404)

#### Check Policy Workspace (assumptions, guardrails, versions)
```bash
curl https://healthforesight-api-9016.azurewebsites.net/api/v1/policies/ST_BIOLOGIC_006/workspace | jq '{assumptions: .assumptions | length, guardrails: .guardrails | length, versions: .versions | length}'
```
Expected: Should show counts > 0 for assumptions, guardrails, and versions

### Step 4: Test Frontend

1. Open Azure Static Web Apps frontend: `https://gentle-flower-01dffcd0f.2.azurestaticapps.net`
2. Navigate to **Policies** page
3. Click on a policy to view workspace
4. Check that **Assumptions**, **Guardrails**, **Versions** tabs have data
5. Check **Predicted Impact** tab (may show "Generate" if not available)
6. Check **Dashboard** - should load without timeouts

## Troubleshooting

### If API still returns 404 for predicted impact:
1. Check if policy has predicted impact data locally:
   ```bash
   cat data/policy_ST_BIOLOGIC_006.json | jq '.predicted_impact'
   ```
2. If data exists locally but not on Azure, the deployment may have failed
3. Re-run `./COMPREHENSIVE_DATA_FIX.sh`

### If API still times out:
1. Check Azure logs:
   ```bash
   az webapp log tail --resource-group healthforesight-rg --name healthforesight-api-9016
   ```
2. Look for file access errors or missing data directory errors
3. Verify `STORAGE_PATH` is set:
   ```bash
   az webapp config appsettings list --resource-group healthforesight-rg --name healthforesight-api-9016 --query "[?name=='STORAGE_PATH']"
   ```
   Expected: `STORAGE_PATH="/home/site/wwwroot/data"`

### If data is still not loading:
1. SSH into Azure App Service:
   ```bash
   az webapp ssh --resource-group healthforesight-rg --name healthforesight-api-9016
   ```
2. Check if data directory exists:
   ```bash
   ls -la /home/site/wwwroot/data/
   ```
3. Check if policy files exist:
   ```bash
   ls -la /home/site/wwwroot/data/policies/
   ls -la /home/site/wwwroot/data/policy_*.json
   ```

## Expected Results After Fix

✅ **Policy Workspace**:
- Assumptions tab shows data
- Guardrails tab shows data
- Versions tab shows data
- Changelog tab shows data

✅ **Predicted Impact**:
- No more 404 errors (or clear "not found" messages)
- Predicted impact loads when available

✅ **Dashboard**:
- No more API timeouts
- Data loads within 30 seconds
- All metrics display correctly

✅ **Other Features**:
- Pipeline monitoring loads
- Data quality dashboard shows data
- Baseline analysis shows latest runs
- Observations load
- What-if scenarios list policies

## Next Steps

After successful deployment:
1. Monitor Azure logs for any errors
2. Test all major features on the frontend
3. Report any remaining issues with specific error messages

