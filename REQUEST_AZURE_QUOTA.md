# How to Request Azure Quota Increase

## Problem

You're getting quota errors even for Free tier App Service Plans:
```
Current Limit (Free VMs): 0
Amount required for this deployment (Free VMs): 1
```

## Solution: Request Quota Increase

### Step 1: Go to Azure Portal

1. Open: https://portal.azure.com
2. Sign in with your Azure account

### Step 2: Navigate to Quota Management

1. **Search for "Subscriptions"** in the top search bar
2. Click on **"Subscriptions"** service
3. Select **your subscription** (the one you're using)

### Step 3: View Usage + Quotas

1. In the left menu, scroll down and click **"Usage + quotas"**
2. You'll see a list of all quotas for your subscription

### Step 4: Find App Service Plans Quota

1. **Filter or search** for "App Service Plans"
2. Look for one of these:
   - **"App Service Plans - Free"** (for F1 tier)
   - **"App Service Plans"** (general - might be this)
   - **"App Service - Free"**
   - **"Compute - App Service Plans"**
   - **"Web Hosting Plans"**

**Note**: If you can't find it here, use **Method 1: Support Request** (see below) instead!

### Step 5: Request Increase

**If you found the quota:**
1. Click on **"App Service Plans - Free"** (or the tier you need)
2. You'll see:
   - **Current Limit**: 0 (or current limit)
   - **Current Usage**: 0
3. Click the **"Request increase"** button at the top

**If you can't find it:**
→ Use Method 1 below (Support Request)
4. Fill out the form:
   - **Subscription**: Your subscription (auto-filled)
   - **Quota type**: App Service Plans - Free
   - **Region**: Select your region (e.g., East US)
   - **New limit**: **1** (minimum) or more
   - **Reason for request**: 
     ```
     Need quota for deploying App Service Plan.
     Deploying HealthForesight platform (FastAPI + React app).
     ```
   - **Additional details**: (optional)
     ```
     Initial deployment for development/testing purposes.
     Will upgrade to Basic/Standard tier after testing.
     ```
5. Click **"Submit"**

### Step 6: Wait for Approval

- **Typical approval time**: 24-48 hours
- **Free tier**: Usually approved quickly (within hours)
- **Basic/Standard tier**: May take longer

### Step 7: Check Status

1. Go back to **Usage + quotas**
2. Check the status of your request
3. Once approved, the limit will update

### Step 8: Retry Deployment

Once quota is approved:

```bash
# Run deployment script again
./DEPLOY_TO_AZURE.sh
```

## Alternative: Upgrade Subscription

If you're on a **Free Account** or limited subscription:

1. Go to: https://portal.azure.com
2. Navigate: **Subscriptions** → Your subscription
3. Click **"Upgrade subscription"**
4. Choose **"Pay-As-You-Go"** (or your preferred plan)
5. Follow the upgrade process

**Note**: Pay-As-You-Go typically has more quota available.

## Method 1: Support Request (RECOMMENDED - Works Even If You Can't Find Quota) ✅

This is the **most reliable method** and works even if you can't find the quota in Usage + Quotas:

### Step 1: Open Support Request

1. Go to: https://portal.azure.com
2. In the top search bar, type: **"Help + support"**
3. Click **"Help + support"** service
4. Click **"+ New support request"** button

### Step 2: Fill Out Support Request

**Problem type:**
- Select: **"Service and subscription limits (quotas)"**

**Subscription:**
- Select your subscription

**Quota type:**
- Select: **"Compute - App Service Plans"** (if available)
- OR: **"Other"** and type "App Service Plans - Free"

**Region:**
- Select your preferred region (e.g., East US)

**Additional details:**
- **Current limit**: 0
- **Requested limit**: 1 (minimum)
- **Tier**: Free (F1)
- **Description**: 
  ```
  Need quota for App Service Plan to deploy application.
  Current limit: 0
  Requested limit: 1
  Tier: Free (F1)
  Reason: Deploying HealthForesight platform for development/testing.
  ```

### Step 3: Submit

Click **"Create"** or **"Submit"**

**Approval time**: Usually 24-48 hours (often faster for Free tier)

This method works even if the quota doesn't appear in Usage + Quotas section!

## What to Request

### For Development/Testing:
- **App Service Plans - Free**: Request 1-2
- **Cost**: $0/month

### For Production:
- **App Service Plans - Basic**: Request 1-2
- **Cost**: ~$13/month per plan
- **OR**
- **App Service Plans - Standard**: Request 1-2
- **Cost**: ~$55/month per plan

## Check Current Quota (via CLI)

```bash
# List all quotas for your subscription
az vm list-usage \
  --location eastus \
  --output table

# Check specific App Service quota (if available)
az quota show \
  --scope "/subscriptions/$(az account show --query id -o tsv)/providers/Microsoft.Compute/locations/eastus" \
  --resource-name "cores" \
  --query properties.limit
```

## Common Issues

### "Quota request denied"
- **Reason**: May need better justification
- **Solution**: Provide more details about your use case

### "Already at maximum"
- **Reason**: Your subscription type has a hard limit
- **Solution**: Upgrade subscription or contact Azure support

### "Request pending for days"
- **Reason**: Standard tier requests may take longer
- **Solution**: Wait or contact Azure support

## After Quota Approval

1. **Verify quota increase**:
   ```bash
   az vm list-usage --location eastus --output table
   ```

2. **Run deployment again**:
   ```bash
   ./DEPLOY_TO_AZURE.sh
   ```

3. **Select your tier**:
   - F1 (Free) - if you requested Free quota
   - B1 (Basic) - if you requested Basic quota

## Summary

✅ **Request quota via Azure Portal** - Usually approved within 24-48 hours
✅ **Free tier requests** - Approved faster (often within hours)
✅ **Upgrade subscription** - Alternative if quota requests are denied
✅ **After approval** - Run deployment script again

**Most quota requests are approved automatically for Free tier within a few hours!**
