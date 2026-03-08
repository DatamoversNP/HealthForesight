"""Azure Blob Storage implementation - for production"""
from typing import BinaryIO, Optional
from datetime import datetime, timedelta
import io

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError

from uepi_common.storage.interface import (
    BlobStorageClient,
    StorageError,
    BlobNotFoundError,
    ContainerNotFoundError,
)


class AzureBlobStorageClient(BlobStorageClient):
    """Azure Blob Storage implementation using native Azure SDK
    
    This implementation uses Azure Storage SDK for optimal performance.
    Connection can be via:
    - Connection string (from environment)
    - Account name + account key
    - Managed Identity (for AKS pods)
    """
    
    def __init__(
        self,
        connection_string: Optional[str] = None,
        account_name: Optional[str] = None,
        account_key: Optional[str] = None,
        account_url: Optional[str] = None,
        use_managed_identity: bool = False,
    ):
        """Initialize Azure Blob Storage client
        
        Args:
            connection_string: Full Azure Storage connection string
            account_name: Storage account name (if not using connection string)
            account_key: Storage account key (if not using connection string)
            account_url: Storage account URL (if not using connection string)
            use_managed_identity: Use Azure Managed Identity (default: False)
            
        Note: For production in AKS, prefer Managed Identity or connection string
        from Key Vault.
        """
        try:
            if connection_string:
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    connection_string
                )
            elif account_name and account_key:
                account_url = account_url or f"https://{account_name}.blob.core.windows.net"
                self.blob_service_client = BlobServiceClient(
                    account_url=account_url,
                    credential=account_key,
                )
            elif use_managed_identity:
                # Use DefaultAzureCredential for Managed Identity
                from azure.identity import DefaultAzureCredential
                if not account_name:
                    raise ValueError("account_name required when using managed identity")
                account_url = account_url or f"https://{account_name}.blob.core.windows.net"
                credential = DefaultAzureCredential()
                self.blob_service_client = BlobServiceClient(
                    account_url=account_url,
                    credential=credential,
                )
            else:
                raise ValueError(
                    "Must provide connection_string, (account_name + account_key), "
                    "or use_managed_identity=True"
                )
        except Exception as e:
            raise StorageError(f"Failed to initialize Azure Blob Storage client: {e}") from e
    
    def upload_blob(
        self,
        container: str,
        blob_name: str,
        data: bytes | BinaryIO,
        content_type: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> str:
        """Upload blob to Azure Blob Storage"""
        try:
            # Create container if it doesn't exist
            self.create_container_if_not_exists(container)
            
            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=container,
                blob=blob_name,
            )
            
            # Convert bytes to file-like if needed
            if isinstance(data, bytes):
                data = io.BytesIO(data)
            
            # Upload with metadata
            upload_kwargs = {
                "data": data,
                "overwrite": True,
            }
            
            if content_type:
                upload_kwargs["content_settings"] = type('obj', (object,), {
                    'content_type': content_type
                })()
            
            if metadata:
                upload_kwargs["metadata"] = {k: str(v) for k, v in metadata.items()}
            
            blob_client.upload_blob(**upload_kwargs)
            
            # Return URL
            return blob_client.url
            
        except Exception as e:
            raise StorageError(f"Failed to upload blob {blob_name}: {e}") from e
    
    def download_blob(
        self,
        container: str,
        blob_name: str,
    ) -> bytes:
        """Download blob from Azure Blob Storage"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container,
                blob=blob_name,
            )
            return blob_client.download_blob().readall()
        except ResourceNotFoundError as e:
            raise BlobNotFoundError(f"Blob {blob_name} not found in container {container}") from e
        except Exception as e:
            raise StorageError(f"Failed to download blob {blob_name}: {e}") from e
    
    def delete_blob(
        self,
        container: str,
        blob_name: str,
    ) -> None:
        """Delete blob from Azure Blob Storage"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container,
                blob=blob_name,
            )
            blob_client.delete_blob()
        except ResourceNotFoundError as e:
            raise BlobNotFoundError(f"Blob {blob_name} not found in container {container}") from e
        except Exception as e:
            raise StorageError(f"Failed to delete blob {blob_name}: {e}") from e
    
    def blob_exists(
        self,
        container: str,
        blob_name: str,
    ) -> bool:
        """Check if blob exists in Azure Blob Storage"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container,
                blob=blob_name,
            )
            blob_client.get_blob_properties()
            return True
        except ResourceNotFoundError:
            return False
        except Exception as e:
            raise StorageError(f"Failed to check blob existence {blob_name}: {e}") from e
    
    def list_blobs(
        self,
        container: str,
        prefix: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> list[str]:
        """List blobs in Azure Blob Storage container"""
        try:
            container_client = self.blob_service_client.get_container_client(container)
            
            # List blobs with prefix filter
            blobs = container_client.list_blobs(name_starts_with=prefix)
            
            blob_names = []
            for blob in blobs:
                blob_names.append(blob.name)
                if max_results and len(blob_names) >= max_results:
                    break
            
            return blob_names
        except ResourceNotFoundError as e:
            raise ContainerNotFoundError(f"Container {container} not found") from e
        except Exception as e:
            raise StorageError(f"Failed to list blobs in container {container}: {e}") from e
    
    def generate_signed_url(
        self,
        container: str,
        blob_name: str,
        expiration_seconds: int = 3600,
    ) -> str:
        """Generate SAS URL for temporary access"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container,
                blob=blob_name,
            )
            
            # Generate SAS token
            from azure.storage.blob import generate_blob_sas, BlobSasPermissions
            from datetime import datetime, timedelta, timezone
            
            sas_token = generate_blob_sas(
                account_name=self.blob_service_client.account_name,
                container_name=container,
                blob_name=blob_name,
                account_key=self.blob_service_client.credential.account_key
                if hasattr(self.blob_service_client.credential, 'account_key')
                else None,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.now(timezone.utc) + timedelta(seconds=expiration_seconds),
            )
            
            return f"{blob_client.url}?{sas_token}"
            
        except Exception as e:
            raise StorageError(f"Failed to generate signed URL for {blob_name}: {e}") from e
    
    def create_container_if_not_exists(
        self,
        container: str,
    ) -> None:
        """Create Azure Blob Storage container if it doesn't exist"""
        try:
            container_client = self.blob_service_client.get_container_client(container)
            container_client.create_container()
        except ResourceExistsError:
            pass  # Container exists, that's fine
        except Exception as e:
            raise StorageError(f"Failed to create container {container}: {e}") from e

