# Comprehensive Data Deployment Fix

## Problem Summary

Multiple data loading issues on Azure:
- ❌ Policy details (assumptions, guardrails, versions) not loading
- ❌ Predicted impacts returning 404
- ❌ Observations not loading
- ❌ Baseline analyses not showing latest runs
- ❌ Pipeline data not loading
- ❌ What-if scenarios not loading
- ❌ API timeouts (30s exceeded)

## Root Cause

**Data files are not being deployed to Azure or the API cannot find them at the expected location.**

The API uses `STORAGE_PATH=/home/site/wwwroot/data` on Azure, but:
1. Data might not be included in deployment ZIP
2. Data might be in wrong location in ZIP
3. STORAGE_PATH might not be set correctly

## Solution

### Step 1: Run Comprehensive Data Fix Script

```bash
./COMPREHENSIVE_DATA_FIX.sh
```

This script:
- ✅ Verifies all local data directories exist
- ✅ Creates deployment package with ALL data files
- ✅ Deploys to Azure with correct STORAGE_PATH
- ✅ Verifies deployment success

### Step 2: Verify Data on Azure

After deployment, verify data is accessible:

```bash
# Check API health
curl https://healthforesight-api-9016.azurewebsites.net/health

# Check if policies are loading
curl https://healthforesight-api-9016.azurewebsites.net/api/v1/policies

# SSH into Azure to check data files
az webapp ssh --resource-group healthforesight-rg --name healthforesight-api-9016
# Then: ls -la /home/site/wwwroot/data/
```

### Step 3: Check API Logs

If issues persist, check logs:

```bash
az webapp log tail --resource-group healthforesight-rg --name healthforesight-api-9016
```

## Data Directories Included

The fix ensures these directories are deployed:
- `data/policies/` - Policy definitions with metadata
- `data/predicted_impacts/` - Predicted impact calculations
- `data/observations/` - Observation records
- `data/baselines/` - Baseline analysis results
- `data/analyses/` - Analysis records
- `data/analysis_results/` - Analysis result files
- `data/pipelines/` - Pipeline definitions
- `data/pipeline_runs/` - Pipeline execution records
- `data/scenarios/` - What-if scenarios
- `data/decisions/` - Decision records
- `data/risks/` - Risk registers
- `data/source_data/` - Source data files

## API Endpoint Fixes

### Predicted Impact Endpoint
- Now returns 404 if predicted impact not found (instead of empty dict)
- Handles both UUID and string policy IDs
- Checks policy metadata for predicted impact data

### CORS Configuration
- Added Azure Static Web Apps domain to allowed origins
- Uses regex pattern to allow all `*.azurestaticapps.net` domains

## Expected Results After Fix

✅ All policy workspace tabs load data (Assumptions, Guardrails, Versions, Changelog)
✅ Predicted impacts load correctly
✅ Observations display properly
✅ Baseline analyses show latest runs
✅ Pipeline monitoring works
✅ What-if scenarios load policies
✅ No more API timeouts (data loads quickly)

## Troubleshooting

If data still doesn't load:

1. **Check STORAGE_PATH is set:**
   ```bash
   az webapp config appsettings list --resource-group healthforesight-rg --name healthforesight-api-9016 --query "[?name=='STORAGE_PATH']"
   ```
   Should be: `/home/site/wwwroot/data`

2. **Check data files exist on Azure:**
   ```bash
   az webapp ssh --resource-group healthforesight-rg --name healthforesight-api-9016
   ls -la /home/site/wwwroot/data/
   ```

3. **Check API logs for errors:**
   ```bash
   az webapp log tail --resource-group healthforesight-rg --name healthforesight-api-9016 | grep -i error
   ```

4. **Verify policy loading:**
   ```bash
   curl https://healthforesight-api-9016.azurewebsites.net/api/v1/policies | jq '.[0] | keys'
   ```

## Next Steps

1. Run `./COMPREHENSIVE_DATA_FIX.sh`
2. Wait 2-3 minutes for deployment to complete
3. Test frontend: https://gentle-flower-01dffcd0f.2.azurestaticapps.net
4. Verify all data loads correctly
5. Check browser console for any remaining errors

