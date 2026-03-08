# Azure File Storage Migration Summary

## ✅ Backup Completed

**Backup Location**: `.backup-core-product/core-product-backup-YYYYMMDD_HHMMSS/`

The complete core product has been backed up before Azure File Storage migration. All source code, configuration, and data files are preserved.

### Backup Verification

```bash
# View backup directory
ls -lh .backup-core-product/core-product-backup-*/

# Verify apps are backed up
ls .backup-core-product/core-product-backup-*/apps/
# Should show: api, web, worker, data
```

## Current Status

### File-Based Storage System

The application currently uses:
- **Local File System**: `./data` directory (configurable via `STORAGE_PATH`)
- **Storage Pattern**: Files organized by tenant_id in subdirectories
- **File Format**: JSON files for most data
- **Storage Modules**: 18+ storage_*.py files for different entities

### Storage Structure

```
data/
├── policies/           # Policy files
├── analyses/          # Analysis results
├── baselines/         # Baseline metrics
├── observations/      # Observation data
├── notifications/     # Notifications
├── scorecards/        # Scorecards
├── exports/           # Export data
├── schedules/         # Scheduled tasks
├── lineage/           # Data lineage
├── learning/          # Learning models
├── tenant_id/         # Tenant-specific data
│   ├── policies/
│   ├── analyses/
│   └── ...
└── ...
```

## Migration Plan: Azure File Storage

### Goal

Keep the file-based architecture **simple** by using Azure File Storage instead of local filesystem.

### Key Difference

**Azure File Storage** (what we'll use):
- SMB file shares (like network drives)
- Simple file operations (read, write, list)
- Can mount as a drive
- Perfect for file-based systems

**Azure Blob Storage** (already exists in codebase):
- Object storage (like S3)
- Different API
- More complex for file-based systems

### Implementation Strategy

1. **Create Azure File Storage Adapter**
   - Drop-in replacement for local filesystem
   - Use `azure-storage-file-share` SDK
   - Same interface as local Path operations

2. **Minimal Changes**
   - Only change storage adapter
   - Keep all existing storage modules unchanged
   - Configuration-based switching

3. **Simple Path Mapping**
   - Local: `./data/tenant_id/policies/policy-123.json`
   - Azure: `tenant_id/policies/policy-123.json`

## Next Steps

### Step 1: Azure File Share Setup

1. Create Azure Storage Account (with File Shares enabled)
2. Create a File Share (e.g., "healthforesight-data")
3. Note account name, account key, and share name

### Step 2: Implementation

1. Add Azure File Storage dependency
2. Create Azure File Storage adapter
3. Update configuration
4. Update storage initialization

### Step 3: Testing

1. Test with Azure File Share
2. Verify all operations work
3. Performance testing

### Step 4: Deployment

1. Deploy to Azure
2. Configure Azure File Share
3. Migrate data (if needed)

## Files to Create/Modify

### New Files (to create)
1. `apps/api/src/uepi_api/storage/azure_file_storage.py` - Azure File Storage adapter

### Modified Files
1. `apps/api/src/uepi_api/config.py` - Add Azure File Storage settings
2. `apps/api/src/uepi_api/storage_file.py` - Add adapter selection
3. `pyproject.toml` - Add `azure-storage-file-share` dependency

### Files NOT Changed
- All `storage_*.py` files - work with adapter
- Router files - no changes
- Worker files - no changes

## Environment Variables

```bash
# Azure File Storage (simple file system)
USE_AZURE_FILE_STORAGE=true
AZURE_STORAGE_ACCOUNT_NAME=yourstorageaccount
AZURE_STORAGE_ACCOUNT_KEY=yourkey
AZURE_STORAGE_FILE_SHARE_NAME=healthforesight-data

# Fallback to local (development)
# USE_AZURE_FILE_STORAGE=false
# STORAGE_PATH=./data
```

## Benefits

✅ **Simple**: Minimal code changes  
✅ **File-Based**: Keep existing architecture  
✅ **Azure**: Cloud-ready storage  
✅ **Scalable**: Azure File Share handles large-scale  
✅ **Flexible**: Can switch between local and Azure  

## Rollback Plan

If needed, restore from backup:
1. Set `USE_AZURE_FILE_STORAGE=false`
2. Use local file system
3. Restore from `.backup-core-product/` if needed

## Documentation

- **Backup Status**: `BACKUP_STATUS.md`
- **Migration Plan**: `AZURE_FILE_STORAGE_MIGRATION_PLAN.md`
- **Implementation Guide**: `AZURE_FILE_STORAGE_IMPLEMENTATION.md`

## Ready to Proceed

The backup is complete and the plan is ready. We can proceed with Azure File Storage implementation while keeping the architecture simple and file-based.
