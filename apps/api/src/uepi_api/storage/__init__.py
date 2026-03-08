"""Storage adapters for file-based storage"""
from typing import Optional

# Import all storage utilities from storage_file.py for backward compatibility
from uepi_api.storage_file import (
    BASE_PATH,
    STORAGE_PATH,
    init_storage,
    policy_storage,
    user_storage,
    tenant_storage,
    analysis_storage,
    analysis_result_index_storage,
)

# Import Azure adapter if available
try:
    from uepi_api.storage.azure_file_storage import AzureFileStorageAdapter
    AZURE_FILE_STORAGE_AVAILABLE = True
except ImportError:
    AZURE_FILE_STORAGE_AVAILABLE = False
    AzureFileStorageAdapter = None  # type: ignore

__all__ = [
    'BASE_PATH',
    'STORAGE_PATH',
    'init_storage',
    'policy_storage',
    'user_storage',
    'tenant_storage',
    'analysis_storage',
    'analysis_result_index_storage',
    'AzureFileStorageAdapter',
    'AZURE_FILE_STORAGE_AVAILABLE',
]
