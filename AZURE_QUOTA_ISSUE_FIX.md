# Azure Quota Issue - Solution Guide

## Issue

When deploying to Azure, you may encounter:
```
Operation cannot be completed without additional quota.
Current Limit (Basic VMs): 0
Amount required for this deployment (Basic VMs): 1
```

## Why This Happens

Azure subscriptions have **quota limits** for different VM sizes and tiers. New subscriptions, especially **free tier** subscriptions, often have:
- **0 quota** for Basic tier (B1, B2)
- **Limited quota** for Standard tier
- **Free quota** for Free tier (F1)

## Solutions

### Solution 1: Use Free Tier (F1) - Quick Fix ✅

The easiest solution is to use the **Free tier (F1)**:

```bash
# Update deployment script or run manually with F1
az appservice plan create \
  --name healthforesight-plan \
  --resource-group healthforesight-rg \
  --location eastus \
  --sku F1 \
  --is-linux
```

**Pros:**
- ✅ Works immediately (no quota needed)
- ✅ Free ($0/month)
- ✅ Good for development/testing

**Cons:**
- ⚠️ CPU throttling (60 minutes/day)
- ⚠️ Always On disabled (app may sleep)
- ⚠️ Limited to 1GB RAM
- ⚠️ Shared resources

### Solution 2: Request Quota Increase - For Production

If you need Basic or Standard tier (recommended for production):

#### Step 1: Check Current Quota

```bash
# List all quota limits
az vm list-usage \
  --location eastus \
  --output table

# Check specific quota
az quota show \
  --scope "/subscriptions/$(az account show --query id -o tsv)/providers/Microsoft.Compute/locations/eastus" \
  --resource-name "cores" \
  --query properties.limit
```

#### Step 2: Request Quota Increase

**Via Azure Portal:**

1. Go to: https://portal.azure.com
2. Search for "Subscriptions"
3. Select your subscription
4. Click "Usage + quotas"
5. Select location (e.g., East US)
6. Find "App Service Plans - Basic" or "Standard"
7. Click "Request increase"
8. Fill out the form:
   - **New Limit**: 1 (or more)
   - **Reason**: "Need quota for App Service deployment"
   - **Details**: Describe your use case
9. Submit the request

**Via Azure CLI:**

```bash
# Get subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Open support request (you'll need to complete in portal)
echo "Go to: https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade/newsupportrequest"
echo "Select: Service and subscription limits (quotas)"
echo "Select: App Service Plans"
echo "Select your location and request increase"
```

**Note:** Quota increases are typically approved within **24-48 hours**.

### Solution 3: Try Different Location

Some Azure regions may have more quota available:

```bash
# Try a different location
LOCATION="westus2"  # or westus, centralus, etc.

az appservice plan create \
  --name healthforesight-plan \
  --resource-group healthforesight-rg \
  --location $LOCATION \
  --sku B1 \
  --is-linux
```

Common locations to try:
- `westus2`
- `westus`
- `centralus`
- `southcentralus`
- `eastus2`

### Solution 4: Upgrade Subscription

If you're on a **free tier subscription**, consider upgrading:

**Azure Free Account:**
- Limited quota
- Free for 12 months
- Some services free forever

**Pay-As-You-Go:**
- More quota available
- Pay only for what you use
- Can request quota increases

**Upgrade via Portal:**
1. Go to: https://portal.azure.com
2. Search for "Subscriptions"
3. Select your subscription
4. Click "Upgrade subscription"
5. Follow the prompts

## Updated Deployment Script

The deployment script now:

1. ✅ **Defaults to Free (F1) tier** to avoid quota issues
2. ✅ **Allows you to choose tier** when running
3. ✅ **Automatically falls back to F1** if quota error occurs
4. ✅ **Provides clear error messages** with solutions

### Running with Free Tier

```bash
./DEPLOY_TO_AZURE.sh
# When prompted for SKU, press Enter for F1 (Free) or type B1/B2
```

### Running with Specific Tier

```bash
# Set SKU environment variable
export APP_SERVICE_SKU=B1
./DEPLOY_TO_AZURE.sh
```

## Comparison: Free vs Basic vs Standard

| Feature | Free (F1) | Basic (B1) | Standard (S1) |
|---------|-----------|------------|---------------|
| **Cost** | $0/month | ~$13/month | ~$55/month |
| **CPU** | Shared, throttled | Dedicated | Dedicated |
| **RAM** | 1GB | 1.75GB | 1.75GB |
| **Always On** | ❌ No | ✅ Yes | ✅ Yes |
| **Scaling** | ❌ No | ❌ No | ✅ Yes |
| **Custom Domain** | ❌ No | ✅ Yes | ✅ Yes |
| **SSL** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Quota** | ✅ Always available | ⚠️ Requires quota | ⚠️ Requires quota |

## Recommendation

### For Development/Testing:
- ✅ **Use Free (F1) tier**
- No quota needed
- Good enough for testing

### For Production:
- ✅ **Request quota increase** for Basic (B1) or Standard (S1)
- Better performance
- Always On enabled
- No CPU throttling

## Quick Fix for Current Deployment

If you're currently stuck with quota error:

1. **Delete existing plan** (if partially created):
   ```bash
   az appservice plan delete \
     --name healthforesight-plan \
     --resource-group healthforesight-rg \
     --yes
   ```

2. **Create with Free tier**:
   ```bash
   az appservice plan create \
     --name healthforesight-plan \
     --resource-group healthforesight-rg \
     --location eastus \
     --sku F1 \
     --is-linux
   ```

3. **Continue deployment** - everything else works the same!

## Summary

✅ **Quick Fix**: Use Free (F1) tier - works immediately
✅ **Production**: Request quota increase for Basic/Standard
✅ **Alternative**: Try different Azure location
✅ **Script Updated**: Now defaults to F1 and handles quota errors gracefully

**Your deployment will work with Free tier - you can always upgrade later!**
