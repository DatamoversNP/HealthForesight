# Quick Fix: App Service Plan Quota Request

## The Issue

App Service Plan quotas are **NOT** managed in the "Usage + quotas" page. They require a **Support Request**.

## Solution: Create Support Request

### Step-by-Step Instructions

1. **Go to Azure Portal Support**:
   - Direct link: https://portal.azure.com/#view/Microsoft_Azure_Support/NewSupportRequestV3Blade
   - Or search "Help + support" → "New support request"

2. **Fill in the Support Request Form**:

   **Basics Tab:**
   - **Problem type**: Select "Service and subscription limits (quotas)"
   - **Subscription**: Select your subscription (Azure subscription 1)
   - **Quota type**: Select "Compute-VM (cores-v3) family" or "App Service Plan"
   - **Support plan**: Select your support plan (Basic/Developer/Standard)

   **Details Tab:**
   - **Severity**: C (Minimal impact) or D (Moderate impact)
   - **Problem description**: 
     ```
     Request quota increase for App Service Plan Basic tier.
     Need 1 core for Basic B1 plan in East US region.
     Current limit: 0 cores
     Requested limit: 1 core
     ```
   - **Additional details**: 
     ```
     Deploying HealthForesight platform API backend.
     Requires Basic tier App Service Plan for production deployment.
     ```

   **Review + create Tab:**
   - Review and click "Create"

3. **Wait for Approval**:
   - Usually approved within 24-48 hours
   - Sometimes instant for small requests
   - You'll receive email notification

## Alternative: Try Creating Plan Directly

Sometimes the quota is available but not shown. Try creating the plan:

```bash
# Set your variables
RESOURCE_GROUP="healthforesight-rg"
LOCATION="eastus"
PLAN_NAME="test-plan"

# Try to create (might work even if quota shows 0)
az appservice plan create \
  --name $PLAN_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku B1
```

If it works, great! If not, you'll get a clearer error message.

## Alternative Solutions (No Quota Needed)

### Option 1: Upload Data Only (Recommended While Waiting)

Upload all your data to Azure File Storage now:

```bash
./deploy-to-azure-free-tier.sh
```

This will:
- ✅ Create Storage Account
- ✅ Upload ALL your data files
- ✅ Create Static Web App (free tier)
- ⏸️ Skip API (wait for quota)

### Option 2: Use Different Region

Some regions have more quota available:

```bash
# Try these regions
LOCATION="westus2" ./deploy-complete-to-azure.sh
# or
LOCATION="centralus" ./deploy-complete-to-azure.sh
# or  
LOCATION="southcentralus" ./deploy-complete-to-azure.sh
```

## Quick Commands

```bash
# Check quota helper
./request-app-service-quota.sh

# Upload data only (no quota needed)
./deploy-to-azure-free-tier.sh

# Try different region
LOCATION="westus2" ./deploy-complete-to-azure.sh
```


