# Data Migration Guide - Azure File Storage

## Overview

This guide helps you migrate all your local data (baselines, observations, predictions, policies, etc.) to Azure File Storage after deploying your application.

## Migration Scripts

Two migration scripts are available:

1. **`migrate-data-to-azure.sh`** - Bash script (uses Azure CLI)
2. **`migrate-data-to-azure.py`** - Python script (uses Azure SDK, more robust)

## Prerequisites

### For Bash Script (`migrate-data-to-azure.sh`):
- ✅ Azure CLI installed
- ✅ Logged into Azure (`az login`)

### For Python Script (`migrate-data-to-azure.py`):
- ✅ Python 3.8+
- ✅ Azure File Share SDK: `pip install azure-storage-file-share`

## Quick Start

### Option 1: Bash Script (Easiest)

```bash
./migrate-data-to-azure.sh
```

The script will prompt you for:
- Resource Group name
- Storage Account name
- File Share name
- Local data directories

### Option 2: Python Script (More Robust)

```bash
# Install dependencies
pip install azure-storage-file-share

# Get storage account key
STORAGE_KEY=$(az storage account keys list \
  --resource-group healthforesight-rg \
  --account-name <your-storage-account> \
  --query "[0].value" -o tsv)

# Run migration
python migrate-data-to-azure.py \
  --account-name <your-storage-account> \
  --account-key "$STORAGE_KEY" \
  --share-name healthforesight-data \
  --data-dir apps/api/data \
  --target-dir apps/api/target_data_model
```

## What Gets Migrated

### Data Directory (`apps/api/data/`)
- ✅ **Baselines** - All baseline analyses
- ✅ **Observations** - All observation records
- ✅ **Policies** - All policy configurations
- ✅ **Analyses** - All analysis results
- ✅ **Learning models** - Elasticity models and accuracy history
- ✅ **Scorecards** - All scorecard data
- ✅ **Ingestions** - Ingestion records
- ✅ **Pipelines** - Pipeline configurations
- ✅ **Curated data** - Curated dataset files
- ✅ **Users & Tenants** - User and tenant configurations
- ✅ **Scenario accuracy** - Scenario accuracy data
- ✅ **Exports** - Export files

### Target Data Model Directory (`apps/api/target_data_model/`)
- ✅ **Target data models** - All CSV files and configurations
- ✅ **Dataset files** - All dataset files organized by tenant

## Directory Structure in Azure File Storage

After migration, your Azure File Storage will have:

```
healthforesight-data/
├── data/
│   ├── baselines/
│   │   ├── 00000000-0000-0000-0000-000000000001/
│   │   │   └── *.json
│   │   └── baselines_index.json
│   ├── observations/
│   │   ├── 00000000-0000-0000-0000-000000000001/
│   │   │   └── *.json
│   │   └── observations_index.json
│   ├── policies/
│   │   └── *.json
│   ├── analyses/
│   ├── learning/
│   │   ├── elasticity_models/
│   │   └── accuracy_history/
│   ├── scorecards/
│   ├── ingestions/
│   ├── pipelines/
│   ├── curated/
│   ├── users/
│   ├── tenants/
│   └── ...
└── target_data_model/
    └── 00000000-0000-0000-0000-000000000001/
        └── *.csv
```

## Step-by-Step Migration

### Step 1: Deploy Application

First, deploy your application (without data):

```bash
./DEPLOY_TO_AZURE.sh
```

### Step 2: Verify Azure File Storage is Configured

Make sure your app has these settings:
- `USE_AZURE_FILE_STORAGE=true`
- `AZURE_STORAGE_ACCOUNT_NAME=<your-storage-account>`
- `AZURE_STORAGE_ACCOUNT_KEY=<your-storage-key>`
- `AZURE_STORAGE_FILE_SHARE_NAME=healthforesight-data`

### Step 3: Run Migration Script

**Using Bash script:**
```bash
./migrate-data-to-azure.sh
```

**Or using Python script:**
```bash
# Get storage key
STORAGE_KEY=$(az storage account keys list \
  --resource-group healthforesight-rg \
  --account-name <your-storage-account> \
  --query "[0].value" -o tsv)

# Run migration
python migrate-data-to-azure.py \
  --account-name <your-storage-account> \
  --account-key "$STORAGE_KEY" \
  --share-name healthforesight-data
```

### Step 4: Verify Migration

**Check in Azure Portal:**
1. Go to: https://portal.azure.com
2. Navigate: **Storage accounts** → Your storage account
3. Click: **File shares** → `healthforesight-data`
4. Browse files to verify uploads

**Check via Azure CLI:**
```bash
# List files
az storage file list \
  --account-name <your-storage-account> \
  --account-key <your-storage-key> \
  --share-name healthforesight-data \
  --path data \
  --recursive \
  --output table
```

**Check via Python script (verify only):**
```bash
python migrate-data-to-azure.py \
  --account-name <your-storage-account> \
  --account-key "$STORAGE_KEY" \
  --share-name healthforesight-data \
  --verify-only
```

### Step 5: Test Application

After migration, test your application:

```bash
# Test health endpoint
curl https://<your-api-app-name>.azurewebsites.net/health

# Test data access
curl https://<your-api-app-name>.azurewebsites.net/api/v1/policies
```

## Advanced Usage

### Upload Specific Directories Only

**Bash script:**
Edit the script to comment out directories you don't want to migrate.

**Python script:**
```bash
# Only migrate policies and observations
python migrate-data-to-azure.py \
  --account-name <account> \
  --account-key <key> \
  --share-name healthforesight-data \
  --data-dir apps/api/data/policies \
  --target-dir ""  # Skip target data model
```

### Resume Failed Uploads

Both scripts are idempotent - you can re-run them safely. They will:
- Skip files that already exist
- Upload only missing files
- Verify uploads at the end

### Migration Progress

The scripts show progress:
- File count per directory
- Upload progress (every 10 files for Python script)
- Final verification

## Troubleshooting

### "Storage account not found"
- Verify storage account name
- Check resource group name
- Ensure you're logged into Azure (`az login`)

### "Permission denied"
- Verify storage account key is correct
- Check if you have access to the storage account

### "File share not found"
- The script will create it automatically
- Or create manually: `az storage share create --account-name <account> --name <share>`

### "Some files failed to upload"
- Check file permissions (read access needed)
- Check file size limits (Azure File Share has limits)
- Re-run the script - it will skip successful uploads

### "Verification shows mismatch"
- Re-run migration for that specific directory
- Check Azure File Storage quotas
- Verify local files haven't changed

## Verification Checklist

After migration, verify:

- [ ] All baseline files uploaded
- [ ] All observation files uploaded
- [ ] All policy files uploaded
- [ ] All analysis files uploaded
- [ ] All learning models uploaded
- [ ] All target data models uploaded
- [ ] Directory structure maintained
- [ ] File sizes match
- [ ] Application can read data from Azure File Storage

## Manual Verification

### Count Files

```bash
# Local
find apps/api/data -type f | wc -l

# Remote (Azure File Storage)
az storage file list \
  --account-name <account> \
  --account-key <key> \
  --share-name healthforesight-data \
  --path data \
  --recursive \
  --query "[].name" -o tsv | wc -l
```

### Compare File Sizes

```bash
# Get a sample file size locally
ls -lh apps/api/data/policies/*.json | head -1

# Get same file size in Azure
az storage file show \
  --account-name <account> \
  --account-key <key> \
  --share-name healthforesight-data \
  --path data/policies/<filename>.json \
  --query "properties.contentLength" -o tsv
```

## Best Practices

1. **Backup First** - Always backup local data before migration
2. **Verify After** - Always verify uploads completed successfully
3. **Test Application** - Test that app can read from Azure File Storage
4. **Monitor Costs** - Azure File Storage costs based on usage
5. **Keep Local Copy** - Keep local backup until you verify everything works

## Cost Considerations

Azure File Storage pricing:
- **Storage**: ~$0.06 per GB/month
- **Transactions**: ~$0.004 per 10,000 operations
- **Data Transfer**: Free (within Azure region)

For 100GB of data:
- **Storage**: ~$6/month
- **Operations**: Minimal (read/write operations)

## Summary

✅ **Migration scripts ready** - Both bash and Python versions
✅ **Automatic upload** - Uploads all data with directory structure
✅ **Verification included** - Verifies uploads match local files
✅ **Idempotent** - Safe to re-run multiple times
✅ **Progress tracking** - Shows upload progress

**Run the migration script after deploying your application to move all data to Azure File Storage!**
