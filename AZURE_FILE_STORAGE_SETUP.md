# Azure File Storage Setup Guide

## ✅ Implementation Complete

The Azure File Storage adapter has been implemented. This guide explains how to set it up and use it.

## Files Created/Modified

### New Files
1. `apps/api/src/uepi_api/storage/azure_file_storage.py` - Azure File Storage adapter
2. `apps/api/src/uepi_api/storage/__init__.py` - Storage adapter exports
3. `apps/api/src/uepi_api/storage_adapter.py` - Storage adapter factory (supports local and Azure)

### Modified Files
1. `apps/api/pyproject.toml` - Added `azure-storage-file-share` dependency
2. `apps/api/src/uepi_api/config.py` - Added Azure File Storage configuration

## Installation

### Step 1: Install Dependencies

```bash
cd apps/api
poetry install
```

This will install `azure-storage-file-share>=12.17.0`.

### Step 2: Create Azure File Share

1. **Create Azure Storage Account** (if not exists):
   - Go to Azure Portal
   - Create Storage Account
   - Enable "File shares" service
   - Note the account name

2. **Create File Share**:
   - In Storage Account, go to "File shares"
   - Click "+ File share"
   - Name: `healthforesight-data` (or your preferred name)
   - Quota: Set as needed (or unlimited)

3. **Get Access Credentials**:
   - Go to "Access keys" in Storage Account
   - Copy "Storage account name"
   - Copy "key1" or "key2"
   - OR create a connection string

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Azure File Storage (enable to use Azure instead of local)
USE_AZURE_FILE_STORAGE=true

# Azure Storage Account (required if using Azure)
AZURE_STORAGE_ACCOUNT_NAME=yourstorageaccount
AZURE_STORAGE_ACCOUNT_KEY=yourkeyhere
AZURE_STORAGE_FILE_SHARE_NAME=healthforesight-data

# OR use connection string instead of account_key:
# AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
```

### Local File Storage (Default)

To use local file storage (current behavior):

```bash
# Use local file system
USE_AZURE_FILE_STORAGE=false
STORAGE_PATH=./data
```

## Usage

### Automatic Adapter Selection

The system automatically selects the storage adapter based on configuration:

```python
from uepi_api.storage_adapter import get_storage_adapter

# Get adapter (Azure or Local based on config)
adapter = get_storage_adapter()

# Use adapter - same interface for both
# Read file
content = adapter.read_text("policies/policy-123.json")
data = adapter.read_json("policies/policy-123.json")

# Write file
adapter.write_text("policies/policy-123.json", content)
adapter.write_json("policies/policy-123.json", data)

# Check existence
if adapter.exists("policies/policy-123.json"):
    # File exists

# Create directory
adapter.mkdir("policies", parents=True)

# List files
files = adapter.list_files("policies", pattern="*.json")

# Delete file
adapter.delete_file("policies/policy-123.json")
```

### Path Mapping

**Local File System**:
- `./data/policies/policy-123.json`

**Azure File Storage**:
- `policies/policy-123.json` (within the file share)

The adapter automatically handles path normalization.

## Migration from Local to Azure

### Step 1: Test with Azure (Staging)

1. Set up Azure File Share (see above)
2. Configure environment variables
3. Test with Azure:
   ```bash
   USE_AZURE_FILE_STORAGE=true
   # ... Azure config ...
   ```

### Step 2: Copy Data to Azure (Optional)

If you have existing local data:

```bash
# Option 1: Use Azure File Share mount (recommended)
# Mount Azure File Share as a drive, then copy files

# Option 2: Use Azure Storage Explorer
# Download from: https://azure.microsoft.com/features/storage-explorer/
# Connect to your storage account
# Copy files from local to Azure File Share

# Option 3: Write a migration script using the adapter
```

### Step 3: Switch to Azure

1. Set `USE_AZURE_FILE_STORAGE=true`
2. Set Azure credentials
3. Restart application

### Step 4: Verify

1. Check that files are accessible
2. Test all operations (read, write, list, delete)
3. Monitor Azure Storage metrics

## Features

### ✅ What Works

- **Read/Write Operations**: Same as local filesystem
- **Directory Operations**: mkdir, list_files, list_directories
- **File Operations**: exists, delete, glob
- **JSON Support**: read_json, write_json
- **Path Normalization**: Automatic path handling

### 📝 Differences from Local

- **No SMB Mount**: Operations via SDK (not mounted drive)
- **Path Format**: Uses forward slashes (Azure standard)
- **Performance**: Network latency (use same Azure region)

## Benefits

✅ **Simple**: Minimal code changes  
✅ **Compatible**: Same interface as local filesystem  
✅ **Scalable**: Azure File Share handles large-scale storage  
✅ **Cloud-Ready**: Ready for Azure deployment  
✅ **Flexible**: Switch between local and Azure via config  

## Troubleshooting

### Error: "azure-storage-file-share is not installed"

```bash
cd apps/api
poetry install
```

### Error: "Azure File Storage is enabled but AZURE_STORAGE_ACCOUNT_NAME is not set"

Set environment variables:
```bash
export USE_AZURE_FILE_STORAGE=true
export AZURE_STORAGE_ACCOUNT_NAME=yourstorageaccount
export AZURE_STORAGE_ACCOUNT_KEY=yourkey
```

### Error: "File not found" or Access Denied

1. Check Azure Storage Account name
2. Verify account key is correct
3. Ensure file share exists
4. Check file share permissions

### Performance Issues

1. Use Azure File Share in same region as application
2. Consider Azure Premium File Shares for better performance
3. Monitor Azure Storage metrics

## Testing

### Test Local Storage

```bash
USE_AZURE_FILE_STORAGE=false
./start-api-server.sh
```

### Test Azure Storage

```bash
USE_AZURE_FILE_STORAGE=true
AZURE_STORAGE_ACCOUNT_NAME=yourstorageaccount
AZURE_STORAGE_ACCOUNT_KEY=yourkey
./start-api-server.sh
```

### Verify Storage

```python
from uepi_api.storage_adapter import get_storage_adapter

adapter = get_storage_adapter()
print(f"Using adapter: {type(adapter).__name__}")

# Test write
adapter.write_text("test/file.txt", "Hello, Azure!")

# Test read
content = adapter.read_text("test/file.txt")
print(f"Content: {content}")

# Test list
files = adapter.list_files("test")
print(f"Files: {files}")
```

## Next Steps

1. ✅ Azure File Storage adapter implemented
2. ✅ Configuration added
3. ✅ Dependency added
4. ⏭️ Test with Azure File Share
5. ⏭️ Migrate data (if needed)
6. ⏭️ Deploy to Azure

## Rollback

To rollback to local file storage:

```bash
USE_AZURE_FILE_STORAGE=false
STORAGE_PATH=./data
```

The local file storage adapter will be used automatically.
