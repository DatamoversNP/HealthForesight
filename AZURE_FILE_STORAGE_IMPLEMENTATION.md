# Azure File Storage Implementation Guide

## Overview

This guide outlines the implementation of Azure File Storage for the HealthForesight project, keeping the file-based architecture simple and straightforward.

## Backup Status

✅ **Backup Created**: Core product backup stored in `.backup-core-product/core-product-backup-YYYYMMDD_HHMMSS/`

This backup preserves the working file-based system before migration.

## Implementation Approach

### Simple Strategy

1. **Create Azure File Storage Adapter**: Drop-in replacement for local filesystem
2. **Keep Existing Code**: Minimal changes to storage modules
3. **Configuration-Based**: Switch between local and Azure via config
4. **No Database**: Continue using file-based storage

### Architecture

```
Current: Local File System → Path operations → JSON files
Future:  Azure File Share → Azure SDK → JSON files
```

The storage adapter will abstract the differences, so existing code doesn't need changes.

## Implementation Steps

### Step 1: Add Azure Dependencies

**File**: `pyproject.toml`

Add:
```toml
[project]
dependencies = [
    ...
    "azure-storage-file-share>=12.17.0",
    "azure-identity>=1.15.0",  # For managed identity support
]
```

### Step 2: Create Azure File Storage Adapter

**File**: `apps/api/src/uepi_api/storage/azure_file_storage.py` (NEW)

This will implement:
- File read/write operations
- Directory listing
- File existence checks
- Directory creation
- Path operations (Azure File Share compatible)

### Step 3: Update Configuration

**File**: `apps/api/src/uepi_api/config.py`

Add Azure File Storage settings:
- `azure_storage_account_name`
- `azure_storage_account_key`
- `azure_storage_file_share_name`
- `azure_storage_connection_string` (alternative)
- `use_azure_file_storage` (flag to switch)

### Step 4: Update Storage Initialization

**File**: `apps/api/src/uepi_api/storage_file.py`

Add adapter selection:
- If `use_azure_file_storage=True` → Use Azure adapter
- If `use_azure_file_storage=False` → Use local filesystem

### Step 5: Path Mapping

**Local**: `./data/tenant_id/policies/policy-123.json`
**Azure**: `tenant_id/policies/policy-123.json`

The Azure adapter will map local paths to Azure File Share paths.

## Key Files to Create/Modify

### New Files
1. `apps/api/src/uepi_api/storage/azure_file_storage.py` - Azure adapter
2. `apps/api/src/uepi_api/storage/__init__.py` - Export adapter

### Modified Files
1. `apps/api/src/uepi_api/config.py` - Add Azure settings
2. `apps/api/src/uepi_api/storage_file.py` - Add adapter selection
3. `pyproject.toml` - Add Azure dependencies

### Files That Don't Need Changes
- All `storage_*.py` files (policies, analyses, etc.) - work with adapter
- Router files - no changes needed
- Worker files - no changes needed

## Azure File Share Setup

### Prerequisites

1. **Azure Storage Account**
   - Create in Azure Portal
   - Enable "File shares" service
   - Note account name and key

2. **File Share**
   - Create a file share (e.g., "healthforesight-data")
   - Set quota if needed
   - Note share name

3. **Access Method**
   - Option 1: Account key (simple, for testing)
   - Option 2: Connection string
   - Option 3: Managed Identity (production, recommended)

### Environment Variables

```bash
# Azure File Storage Configuration
USE_AZURE_FILE_STORAGE=true
AZURE_STORAGE_ACCOUNT_NAME=yourstorageaccount
AZURE_STORAGE_ACCOUNT_KEY=yourkey
AZURE_STORAGE_FILE_SHARE_NAME=healthforesight-data
# OR use connection string:
# AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...

# Fallback to local (for development)
# USE_AZURE_FILE_STORAGE=false
# STORAGE_PATH=./data
```

## Benefits

1. **Simple**: Minimal code changes
2. **Scalable**: Azure File Share handles large-scale storage
3. **Compatible**: Same file-based architecture
4. **Flexible**: Can switch between local and Azure
5. **Cloud-Ready**: Ready for Azure deployment

## Migration Path

### Phase 1: Development (Current)
- Use local file system
- Test with Azure File Share in parallel

### Phase 2: Testing
- Test with Azure File Share
- Verify all operations work
- Performance testing

### Phase 3: Production
- Switch to Azure File Share
- Monitor performance
- Keep local as backup option

## Testing Strategy

1. **Local Testing**: Continue using local filesystem
2. **Azure Testing**: Test with Azure File Share (staging)
3. **Parallel Running**: Both storage methods work simultaneously
4. **Data Migration**: Copy data from local to Azure when ready

## Next Steps

1. ✅ Create backup of core product
2. ✅ Document current structure
3. ⏭️ Add Azure dependencies
4. ⏭️ Create Azure File Storage adapter
5. ⏭️ Update configuration
6. ⏭️ Test with Azure File Share
7. ⏭️ Deploy to Azure

## Rollback Plan

If Azure migration has issues:
1. Set `USE_AZURE_FILE_STORAGE=false`
2. Use local file system
3. Restore from backup if needed

The backup in `.backup-core-product/` preserves the working system.
