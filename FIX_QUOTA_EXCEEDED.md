# Fix: Azure App Service QuotaExceeded Error

## Problem

Getting `QuotaExceeded` error when trying to start the app:
```
QuotaExceeded
```

This means the App Service has exceeded quota limits (CPU, memory, storage, etc.).

## Common Causes

### 1. Free Tier (F1) Limits
- **CPU Time**: 60 minutes/day (shared)
- **Memory**: 1GB limit
- **Storage**: 1GB limit
- **Always On**: Disabled (app may stop)
- **Auto-sleep**: After 20 minutes of inactivity

### 2. Basic Tier Limits
- Less likely, but possible if hitting resource limits
- Check specific quota in portal

## Solutions

### Solution 1: Check Current Tier and Limits

```bash
# Check current tier
az appservice plan show \
  --name healthforesight-plan \
  --resource-group healthforesight-rg \
  --query sku -o json

# Check app service details
az webapp show \
  --name hf-api8755146 \
  --resource-group healthforesight-rg \
  --query "{state: state, sku: sku, usage: usageState}" -o json
```

### Solution 2: Upgrade to Basic Tier (Recommended)

If you're on Free tier (F1), upgrade to Basic (B1) for better limits:

```bash
# Scale up to Basic tier
az appservice plan update \
  --name healthforesight-plan \
  --resource-group healthforesight-rg \
  --sku B1

# Then start the app
az webapp start \
  --name hf-api8755146 \
  --resource-group healthforesight-rg
```

**Cost**: ~$13/month, but removes most quota limits

### Solution 3: Check Specific Quota

Check what quota is exceeded:

**Via Azure Portal:**
1. Go to: https://portal.azure.com
2. Navigate: **App Services** → `hf-api8755146`
3. Click: **Metrics** (left menu)
4. Check: CPU usage, Memory usage, etc.

**Via CLI:**
```bash
# Check metrics
az monitor metrics list \
  --resource /subscriptions/$(az account show --query id -o tsv)/resourceGroups/healthforesight-rg/providers/Microsoft.Web/sites/hf-api8755146 \
  --metric "CpuPercentage,MemoryPercentage" \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --interval PT1H
```

### Solution 4: Wait for Quota Reset (Free Tier Only)

If you're on Free tier, quotas reset daily:
- **CPU Time**: Resets every 24 hours
- **Storage**: Check if you're using too much

**Wait 24 hours** and try again, or upgrade to Basic tier.

### Solution 5: Check App Settings

Ensure Always On is enabled (Basic tier only):

```bash
# Enable Always On (only works on Basic+)
az webapp config set \
  --name hf-api8755146 \
  --resource-group healthforesight-rg \
  --always-on true
```

**Note**: Always On is only available on Basic tier and above.

### Solution 6: Scale Down Other Apps (If Multiple Apps)

If you have multiple apps on the same App Service Plan:

```bash
# List all apps in the plan
az webapp list \
  --query "[?appServicePlanId=='/subscriptions/$(az account show --query id -o tsv)/resourceGroups/healthforesight-rg/providers/Microsoft.Web/serverfarms/healthforesight-plan'].name" \
  -o table

# Stop unused apps to free quota
az webapp stop \
  --name <other-app-name> \
  --resource-group healthforesight-rg
```

## Quick Diagnostic

```bash
# 1. Check tier
az appservice plan show \
  --name healthforesight-plan \
  --resource-group healthforesight-rg \
  --query "sku.name" -o tsv

# 2. Check app state
az webapp show \
  --name hf-api8755146 \
  --resource-group healthforesight-rg \
  --query "{state: state, sku: sku}" -o json

# 3. Check if Always On is enabled
az webapp config show \
  --name hf-api8755146 \
  --resource-group healthforesight-rg \
  --query "alwaysOn" -o tsv
```

## Recommended Action

### If on Free Tier (F1):

**Option 1: Upgrade to Basic (B1) - Recommended**
```bash
# Upgrade plan to Basic
az appservice plan update \
  --name healthforesight-plan \
  --resource-group healthforesight-rg \
  --sku B1

# Start app
az webapp start \
  --name hf-api8755146 \
  --resource-group healthforesight-rg
```

**Option 2: Wait for Quota Reset**
- Quota resets every 24 hours
- Or wait until next billing cycle

### If on Basic Tier (B1):

Check specific quota limits:
- Go to Azure Portal → Your App Service → **Metrics**
- Check CPU, Memory, Storage usage
- Consider scaling up to B2 or S1 if hitting limits

## Check Usage in Azure Portal

1. Go to: https://portal.azure.com
2. Navigate: **App Services** → `hf-api8755146`
3. Click: **Metrics** (left menu)
4. Check:
   - **CPU Percentage**
   - **Memory Percentage**
   - **Http Server Errors**
   - **Requests**

## Summary

✅ **QuotaExceeded** - App Service hit quota limits
✅ **Check tier** - Free tier has strict limits
✅ **Upgrade to Basic** - Recommended solution (~$13/month)
✅ **Or wait** - Quota resets daily (Free tier only)

**Most likely solution: Upgrade to Basic tier (B1) to remove quota limits.**
