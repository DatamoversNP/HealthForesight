# Azure File Storage Migration Plan

## Overview

This document outlines the plan to migrate the file-based storage system to Azure File Storage while keeping the architecture simple and file-based.

## Current Architecture

### File Storage Structure

The application currently uses local file system storage:
- **Base Path**: `./data` (configurable via `STORAGE_PATH` env var)
- **Storage Pattern**: Files organized by tenant_id in subdirectories
- **File Format**: JSON files for most data
- **Storage Modules**: Multiple storage_*.py files for different entities

### Current Storage Modules

1. **storage_policies.py** - Policy storage
2. **storage_analyses.py** - Analysis results
3. **storage_baselines.py** - Baseline metrics
4. **storage_observations.py** - Observation data
5. **storage_notifications.py** - Notifications
6. **storage_scorecards.py** - Scorecards
7. **storage_exports.py** - Export data
8. **storage_schedules.py** - Scheduled tasks
9. **storage_lineage.py** - Data lineage
10. **storage_learning.py** - Learning models
11. **storage_policy_predicted_impact.py** - Predicted impacts
12. **storage_scenario_accuracy.py** - Scenario accuracy
13. **storage_data_periods.py** - Data periods
14. **storage_policy_versions.py** - Policy versions
15. **storage_ingestions.py** - Ingestion data
16. **storage_pipelines.py** - Pipeline definitions
17. **storage_pipeline_runs.py** - Pipeline run results
18. **storage_file.py** - Base file storage utilities

## Migration Strategy

### Phase 1: Create Azure File Storage Adapter (Simple Approach)

**Goal**: Create a drop-in replacement for local file system that uses Azure File Storage.

**Approach**: 
- Create `AzureFileStorageAdapter` that implements the same interface as local file system
- Use Azure Files SDK (`azure-storage-file-share`)
- Keep all existing storage modules unchanged
- Only change the base storage adapter

### Phase 2: Configuration

**Changes Needed**:
1. Add Azure File Storage configuration to `config.py`
2. Environment variables for Azure credentials:
   - `AZURE_STORAGE_ACCOUNT_NAME`
   - `AZURE_STORAGE_ACCOUNT_KEY`
   - `AZURE_STORAGE_FILE_SHARE_NAME`
   - `AZURE_STORAGE_CONNECTION_STRING` (alternative to account/key)

### Phase 3: Implementation

**Files to Create**:
1. `apps/api/src/uepi_api/storage/azure_file_storage.py` - Azure File Storage adapter
2. `apps/api/src/uepi_api/storage/__init__.py` - Update to support Azure

**Files to Modify**:
1. `apps/api/src/uepi_api/config.py` - Add Azure File Storage settings
2. `apps/api/src/uepi_api/storage_file.py` - Add Azure adapter option
3. `pyproject.toml` - Add `azure-storage-file-share` dependency

### Phase 4: Testing

1. Test with local file system (current)
2. Test with Azure File Storage (new)
3. Ensure both work seamlessly

## Implementation Details

### Azure File Storage Adapter Interface

```python
class AzureFileStorageAdapter:
    def __init__(self, account_name: str, account_key: str, share_name: str):
        # Initialize Azure File Share client
        
    def read_file(self, path: str) -> bytes:
        # Read file from Azure File Share
        
    def write_file(self, path: str, content: bytes):
        # Write file to Azure File Share
        
    def list_files(self, path: str) -> List[str]:
        # List files in Azure File Share directory
        
    def delete_file(self, path: str):
        # Delete file from Azure File Share
        
    def exists(self, path: str) -> bool:
        # Check if file exists in Azure File Share
        
    def mkdir(self, path: str):
        # Create directory in Azure File Share (if needed)
```

### Key Considerations

1. **Path Mapping**: 
   - Local: `./data/tenant_id/policies/`
   - Azure: `tenant_id/policies/`

2. **File Operations**:
   - Azure File Share supports standard file operations
   - Similar to local file system but via SDK

3. **Performance**:
   - Azure File Share provides SMB access (can mount as drive)
   - SDK access for programmatic operations

4. **Simplicity**:
   - Keep existing storage modules unchanged
   - Only swap the underlying adapter

5. **Backward Compatibility**:
   - Support both local and Azure via configuration
   - Default to local for development

## Migration Steps

### Step 1: Backup Current System ✓
- [x] Create backup of core product
- [x] Document current structure

### Step 2: Add Azure Dependencies
- [ ] Add `azure-storage-file-share` to `pyproject.toml`
- [ ] Install dependencies

### Step 3: Create Azure Adapter
- [ ] Create `azure_file_storage.py`
- [ ] Implement file operations (read, write, list, delete, exists)
- [ ] Test with Azure File Share

### Step 4: Update Configuration
- [ ] Add Azure settings to `config.py`
- [ ] Add environment variables documentation
- [ ] Add Azure vs Local selection logic

### Step 5: Update Storage Initialization
- [ ] Update `storage_file.py` to support Azure adapter
- [ ] Add storage adapter selection (local vs Azure)
- [ ] Ensure backward compatibility

### Step 6: Testing
- [ ] Test all storage operations with Azure
- [ ] Verify data integrity
- [ ] Performance testing

### Step 7: Documentation
- [ ] Update deployment docs
- [ ] Add Azure File Share setup guide
- [ ] Add migration guide

## Benefits of This Approach

1. **Simple**: Minimal changes to existing code
2. **Maintainable**: Clear separation of concerns
3. **Flexible**: Can switch between local and Azure
4. **Testable**: Easy to test both storage backends
5. **Scalable**: Azure File Share supports large-scale storage

## Risks and Mitigation

1. **Risk**: Azure File Share latency
   - **Mitigation**: Use Azure File Share in same region as application

2. **Risk**: Network issues
   - **Mitigation**: Implement retry logic and error handling

3. **Risk**: Cost implications
   - **Mitigation**: Monitor usage and optimize storage

## Next Steps

1. Review and approve this plan
2. Create Azure File Share in Azure Portal
3. Get Azure Storage credentials
4. Start implementation
