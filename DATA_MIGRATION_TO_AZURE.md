# Data Migration to Azure File Storage

## Important: Data is NOT Included in Deployment ZIP

### Current Deployment Behavior

The deployment script **excludes data files** from the deployment ZIP:

- ❌ **data/** directory - Excluded from ZIP
- ❌ **target_data_model/** directory - Excluded from ZIP  
- ✅ **src/** directory - Included (your application code)
- ✅ **requirements.txt** - Included (dependencies)

### Why Data is Excluded

1. **Large file size** - Data files can be large, deployment ZIPs have size limits
2. **Azure File Storage** - Data should be stored in Azure File Storage, not in the app package
3. **Separate migration** - Data migration is a separate step from code deployment
4. **Better practice** - Code and data should be separate

## What Gets Deployed

### ✅ Included in Deployment:
- Application code (`src/` directory)
- Configuration files (`pyproject.toml`, `requirements.txt`)
- Startup scripts
- Application logic

### ❌ NOT Included:
- **Data files** (baselines, observations, predictions, etc.)
- **Target data models**
- **Test data**
- **Local storage files**

## Data That Needs Migration

Based on your project structure, these need to be migrated:

1. **Baselines** (`apps/api/data/baselines/`)
2. **Observations** (`apps/api/data/observations/`)
3. **Policies** (`apps/api/data/policies/`)
4. **Analyses** (`apps/api/data/analyses/`)
5. **Learning models** (`apps/api/data/learning/`)
6. **Scorecards** (`apps/api/data/scorecards/`)
7. **Ingestions** (`apps/api/data/ingestions/`)
8. **Target data models** (`apps/api/target_data_model/`)
9. **Users and tenants** (`apps/api/data/users/`, `apps/api/data/tenants/`)

## Solution: Migrate Data to Azure File Storage

### Step 1: Deploy Application First

1. **Deploy the application** (without data):
   ```bash
   ./DEPLOY_TO_AZURE.sh
   ```

2. **Verify application is running**:
   ```bash
   curl https://<your-api-app-name>.azurewebsites.net/health
   ```

### Step 2: Migrate Data to Azure File Storage

Once the application is deployed and Azure File Storage is configured, migrate your data:

#### Option A: Using Azure CLI (Recommended)

```bash
# Set your variables
STORAGE_ACCOUNT="<your-storage-account-name>"
STORAGE_KEY="<your-storage-key>"
FILE_SHARE_NAME="healthforesight-data"
RESOURCE_GROUP="healthforesight-rg"

# Get storage key
STORAGE_KEY=$(az storage account keys list \
  --resource-group $RESOURCE_GROUP \
  --account-name $STORAGE_ACCOUNT \
  --query "[0].value" -o tsv)

# Upload data directory
az storage file upload-batch \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --source apps/api/data \
  --destination $FILE_SHARE_NAME/data \
  --destination-path data

# Upload target data models
az storage file upload-batch \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --source apps/api/target_data_model \
  --destination $FILE_SHARE_NAME/target_data_model \
  --destination-path target_data_model
```

#### Option B: Using Azure Portal

1. Go to: https://portal.azure.com
2. Navigate: **Storage accounts** → Your storage account
3. Click: **File shares** → Your file share (`healthforesight-data`)
4. Click: **Upload** and select your data files
5. Create folders as needed (data/, target_data_model/, etc.)

#### Option C: Using Python Script (Automated)

I can create a migration script that:
- Reads all data from local file system
- Uploads to Azure File Storage
- Maintains directory structure
- Verifies uploads

Would you like me to create this migration script?

### Step 3: Verify Data Migration

After migration, verify the data is accessible:

```bash
# List files in Azure File Storage
az storage file list \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --share-name $FILE_SHARE_NAME \
  --path data \
  --output table
```

## Automated Data Migration Script

I can create a script to automate this process. Would you like me to create:

1. **Migration script** - Uploads all data to Azure File Storage
2. **Verification script** - Checks that all data was migrated correctly
3. **Sync script** - Keeps local and Azure data in sync

## Configuration Files

Some configuration files might also need migration:

- **Users** (`apps/api/data/users/`)
- **Tenants** (`apps/api/data/tenants/`)
- **Pipelines** (`apps/api/data/pipelines/`)

These should be migrated along with the data.

## Recommended Approach

### Phase 1: Deploy Application ✅
```bash
./DEPLOY_TO_AZURE.sh
```
- Deploys code only
- Sets up Azure File Storage
- Application starts (empty data initially)

### Phase 2: Migrate Data ✅
```bash
# Use migration script or Azure CLI
# Upload all data to Azure File Storage
```

### Phase 3: Verify ✅
- Check application can read data from Azure File Storage
- Verify baselines, observations, predictions are accessible
- Test application functionality

## Alternative: Include Data in Deployment (Not Recommended)

If you really want to include data in the deployment ZIP:

```bash
# Modify the deployment script to NOT exclude data
# Remove: -x "data/*" and -x "target_data_model/*"
```

**⚠️ Warning**: This is NOT recommended because:
- Deployment ZIPs have size limits (~200MB)
- Data files can be very large
- Code deployments should be fast
- Data should be separate from code

## Summary

✅ **Application code** - Included in deployment
❌ **Data files** - NOT included (excluded intentionally)
✅ **Azure File Storage** - Configured and ready
✅ **Migration needed** - Data must be uploaded separately

**Next Step**: Deploy application first, then migrate data to Azure File Storage.

Would you like me to create an automated data migration script?
