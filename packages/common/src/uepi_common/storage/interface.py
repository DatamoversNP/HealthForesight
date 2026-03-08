"""Blob storage abstraction interface - cloud-portable"""
from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
from pathlib import Path


class BlobStorageClient(ABC):
    """Abstract interface for blob storage operations
    
    This interface ensures cloud portability - implementations can use:
    - Azure Blob Storage (prod)
    - AWS S3 (prod)
    - MinIO (dev)
    - Local filesystem (dev/testing)
    
    All implementations must follow this interface exactly.
    """
    
    @abstractmethod
    def upload_blob(
        self,
        container: str,
        blob_name: str,
        data: bytes | BinaryIO,
        content_type: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> str:
        """Upload a blob to storage
        
        Args:
            container: Container/bucket name
            blob_name: Path within container (e.g., 'policies/tenant_id/policy.json')
            data: Blob content as bytes or file-like object
            content_type: MIME type (e.g., 'application/json', 'application/parquet')
            metadata: Optional metadata key-value pairs
            
        Returns:
            URL/path to the uploaded blob
            
        Raises:
            StorageError: If upload fails
        """
        pass
    
    @abstractmethod
    def download_blob(
        self,
        container: str,
        blob_name: str,
    ) -> bytes:
        """Download a blob from storage
        
        Args:
            container: Container/bucket name
            blob_name: Path within container
            
        Returns:
            Blob content as bytes
            
        Raises:
            BlobNotFoundError: If blob doesn't exist
            StorageError: If download fails
        """
        pass
    
    @abstractmethod
    def delete_blob(
        self,
        container: str,
        blob_name: str,
    ) -> None:
        """Delete a blob from storage
        
        Args:
            container: Container/bucket name
            blob_name: Path within container
            
        Raises:
            BlobNotFoundError: If blob doesn't exist
            StorageError: If deletion fails
        """
        pass
    
    @abstractmethod
    def blob_exists(
        self,
        container: str,
        blob_name: str,
    ) -> bool:
        """Check if a blob exists
        
        Args:
            container: Container/bucket name
            blob_name: Path within container
            
        Returns:
            True if blob exists, False otherwise
        """
        pass
    
    @abstractmethod
    def list_blobs(
        self,
        container: str,
        prefix: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> list[str]:
        """List blobs in a container
        
        Args:
            container: Container/bucket name
            prefix: Optional prefix filter (e.g., 'policies/tenant_id/')
            max_results: Optional limit on number of results
            
        Returns:
            List of blob names (paths) matching the criteria
        """
        pass
    
    @abstractmethod
    def generate_signed_url(
        self,
        container: str,
        blob_name: str,
        expiration_seconds: int = 3600,
    ) -> str:
        """Generate a signed URL for temporary access to a blob
        
        Args:
            container: Container/bucket name
            blob_name: Path within container
            expiration_seconds: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Signed URL that can be used for direct access
            
        Raises:
            StorageError: If URL generation fails
        """
        pass
    
    @abstractmethod
    def create_container_if_not_exists(
        self,
        container: str,
    ) -> None:
        """Create a container/bucket if it doesn't exist
        
        Args:
            container: Container/bucket name
            
        Raises:
            StorageError: If creation fails
        """
        pass


class StorageError(Exception):
    """Base exception for storage operations"""
    pass


class BlobNotFoundError(StorageError):
    """Raised when a blob is not found"""
    pass


class ContainerNotFoundError(StorageError):
    """Raised when a container/bucket is not found"""
    pass

