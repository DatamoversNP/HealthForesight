# Azure Quota Issue - Fix Guide

## Problem

You're hitting a quota limit for Basic VMs in your Azure subscription:
- **Current Limit**: 0 Basic VMs
- **Required**: 1 Basic VM (for App Service Plan)
- **Status**: Cannot create App Service Plan without quota increase

## Solution Options

### Option 1: Request Quota Increase (Recommended)

#### Method A: Via Azure Portal (Easiest)

1. **Go to Azure Portal**: https://portal.azure.com
2. **Navigate to Subscriptions**:
   - Search for "Subscriptions" in the top search bar
   - Click on your subscription
3. **Request Quota Increase**:
   - Click on "Usage + quotas" in the left menu
   - Search for "App Service Plan" or "Basic"
   - Click "Request increase"
   - Fill in:
     - **Quota type**: App Service Plan - Basic
     - **Region**: Your deployment region (e.g., eastus)
     - **New limit**: 1 (or more if you need multiple)
   - Click "Submit"
4. **Wait for Approval**:
   - Usually approved within 24-48 hours
   - Sometimes instant for small increases

#### Method B: Via Azure CLI

```bash
# Login first
az login

# Get your subscription ID
az account show --query id -o tsv

# Request quota increase (replace with your subscription ID and region)
az vm list-usage \
  --location eastus \
  --output table

# Note: Quota increases must be requested via Portal or Support
```

#### Method C: Contact Azure Support

1. Go to Azure Portal → Help + Support
2. Create a new support request
3. Select:
   - **Issue type**: Service and subscription limits (quotas)
   - **Subscription**: Your subscription
   - **Quota type**: Compute-VM (cores-v3) family
   - **Region**: Your deployment region
4. Request 1-2 cores for Basic tier

### Option 2: Use Free Tier (No Quota Required)

Deploy using Azure Static Web Apps (free tier) and Azure Functions (free tier):

```bash
# This doesn't require App Service Plan quota
# We'll modify the deployment script to use free services
```

### Option 3: Use Different Region

Some regions have more available quota:

```bash
# Try a different region
LOCATION="westus2"  # or "centralus", "southcentralus"
```

### Option 4: Use Consumption Plan (Serverless)

Use Azure Functions or Container Apps with consumption plan (no quota limits).

## Quick Fix Script

I'll create a modified deployment script that:
1. Checks quota first
2. Suggests alternative regions
3. Uses free tier options if available

## Immediate Actions

1. **Request quota increase via Portal** (fastest):
   - https://portal.azure.com → Subscriptions → Usage + quotas → Request increase

2. **Or use the modified deployment script** that uses free tier services

3. **Or try a different region** with available quota

## Check Current Quota

```bash
# Check quota for your region
az vm list-usage \
  --location eastus \
  --output table

# Check App Service quotas
az appservice list-locations \
  --sku Basic \
  --output table
```


