# Azure Deployment Checklist

## Pre-Deployment Checks

### ✅ Code Fixes Included
- [x] localStorage quota fix (logger.ts)
- [x] DOM nesting warning fix (ExecutiveDashboardPage.tsx)
- [x] Logging system integration
- [x] Error tracking system

### ✅ Files to Deploy
- [x] API code with all fixes
- [x] Web code with all fixes
- [x] Policy files with embedded metadata
- [x] packages/common
- [x] requirements.txt with all dependencies

### ✅ Environment Variables
- [x] STORAGE_PATH configured
- [x] Logging enabled
- [x] Python dependencies included

## Deployment Steps

1. **Run deployment script:**
   ```bash
   ./START_PRODUCTION_BUILD.sh
   ```

2. **Script will:**
   - Check prerequisites (Azure CLI, zip)
   - Detect existing Azure resources
   - Build API deployment package
   - Build Web deployment package
   - Deploy to Azure App Service

3. **Verify deployment:**
   - Check API health: `https://[API_APP_NAME].azurewebsites.net/health`
   - Check Web: `https://[WEB_APP_NAME].azurewebsites.net`
   - Check logs in Azure Portal

## Post-Deployment Verification

- [ ] API responds to health check
- [ ] Web application loads
- [ ] Policies load correctly
- [ ] Logging works (check Azure logs)
- [ ] No console errors in browser

## Rollback Plan

If deployment fails:
1. Check Azure Portal logs
2. Review deployment script output
3. Check environment variables
4. Verify data files are included

