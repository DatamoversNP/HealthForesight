"""Factory for creating storage clients based on configuration"""
from typing import Optional

from uepi_common.storage.interface import BlobStorageClient
from uepi_common.storage.local import LocalBlobStorageClient
# Azure storage (optional - only needed for Azure deployments)
try:
    from uepi_common.storage.azure import AzureBlobStorageClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    AzureBlobStorageClient = None
try:
    from uepi_common.config import ObjectStorageSettings
except ImportError:
    # For type hints only - actual usage will have config
    ObjectStorageSettings = None


def get_blob_storage_client(
    settings: Optional[ObjectStorageSettings] = None,
    endpoint_url: Optional[str] = None,
    connection_string: Optional[str] = None,
    use_azure: bool = False,
) -> BlobStorageClient:
    """Get blob storage client (alias for create_storage_client for compatibility)"""
    return create_storage_client(settings, endpoint_url, connection_string, use_azure)


def create_storage_client(
    settings: Optional[ObjectStorageSettings] = None,
    endpoint_url: Optional[str] = None,
    connection_string: Optional[str] = None,
    use_azure: bool = False,
) -> BlobStorageClient:
    """Create appropriate storage client based on configuration
    
    Args:
        settings: ObjectStorageSettings instance (optional)
        endpoint_url: Override endpoint URL (for local/MinIO)
        connection_string: Azure connection string (for Azure)
        use_azure: Force Azure Blob Storage (default: auto-detect)
        
    Returns:
        BlobStorageClient implementation (Azure or Local/MinIO)
        
    Examples:
        # Local development with MinIO
        client = create_storage_client(
            endpoint_url="http://localhost:9000",
            settings=ObjectStorageSettings(
                access_key="admin",
                secret_key="admin123",
                bucket_name="uepi-data",
            )
        )
        
        # Production with Azure
        client = create_storage_client(
            connection_string=os.getenv("AZURE_STORAGE_CONNECTION_STRING"),
        )
        
        # Production with Azure Managed Identity
        client = create_storage_client(
            account_name="uepistorage",
            use_azure=True,
            use_managed_identity=True,
        )
    """
    # If connection string provided, use Azure (if available)
    if connection_string or use_azure:
        if not AZURE_AVAILABLE:
            raise ValueError("Azure storage is not available. Install azure-storage-blob package.")
        if connection_string:
            return AzureBlobStorageClient(connection_string=connection_string)
        else:
            # Use Managed Identity or account key from settings
            if settings:
                return AzureBlobStorageClient(
                    account_name=settings.bucket_name_or_bucket,
                    account_key=settings.secret_access_key_or_secret_key,
                    use_managed_identity=False,  # Set True in production with MI
                )
            else:
                raise ValueError("Must provide connection_string or settings for Azure")
    
    # Determine endpoint URL
    if settings:
        endpoint = endpoint_url or settings.endpoint_url_or_none
    else:
        endpoint = endpoint_url
    
    # If endpoint URL is provided, use Local/MinIO client
    if endpoint:
        if not settings:
            raise ValueError("Must provide settings for local/MinIO storage")
        return LocalBlobStorageClient(
            endpoint_url=endpoint,
            access_key_id=settings.access_key_id_or_access_key,
            secret_access_key=settings.secret_access_key_or_secret_key,
            use_ssl=settings.use_ssl,
            region=settings.region,
        )
    
    # Default: check environment for Azure connection string
    import os
    azure_conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if azure_conn_str:
        if not AZURE_AVAILABLE:
            raise ValueError("Azure storage is not available. Install azure-storage-blob package.")
        return AzureBlobStorageClient(connection_string=azure_conn_str)
    
    # Fallback: local MinIO with default settings
    if settings:
        return LocalBlobStorageClient(
            endpoint_url="http://localhost:9000",
            access_key_id=settings.access_key_id_or_access_key or "admin",
            secret_access_key=settings.secret_access_key_or_secret_key or "admin123",
            use_ssl=False,
        )
    
    raise ValueError(
        "Cannot determine storage client type. Provide connection_string, "
        "endpoint_url with settings, or set AZURE_STORAGE_CONNECTION_STRING"
    )

