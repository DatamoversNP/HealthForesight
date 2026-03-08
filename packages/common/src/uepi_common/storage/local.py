"""Local/MinIO blob storage implementation - for development and testing"""
import os
from pathlib import Path
from typing import BinaryIO, Optional
from datetime import datetime, timedelta
from urllib.parse import quote

import boto3
from botocore.exceptions import ClientError

from uepi_common.storage.interface import (
    BlobStorageClient,
    StorageError,
    BlobNotFoundError,
    ContainerNotFoundError,
)


class LocalBlobStorageClient(BlobStorageClient):
    """Local/MinIO blob storage implementation using S3-compatible API
    
    Supports:
    - MinIO for local development
    - Any S3-compatible storage (localstack, etc.)
    - AWS S3 (if endpoint_url is None)
    
    This implementation uses boto3 S3 client for portability.
    """
    
    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        use_ssl: bool = False,
        region: str = "us-east-1",
    ):
        """Initialize local/S3-compatible storage client
        
        Args:
            endpoint_url: MinIO/S3-compatible endpoint (e.g., 'http://localhost:9000')
                         If None, uses AWS S3
            access_key_id: Access key (MinIO root user or AWS access key)
            secret_access_key: Secret key (MinIO root password or AWS secret key)
            use_ssl: Whether to use SSL/TLS
            region: AWS region (ignored for MinIO)
        """
        self.endpoint_url = endpoint_url
        self.use_ssl = use_ssl
        
        # Initialize S3 client
        client_kwargs = {
            "region_name": region,
        }
        
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url
            client_kwargs["use_ssl"] = use_ssl
        
        if access_key_id and secret_access_key:
            client_kwargs["aws_access_key_id"] = access_key_id
            client_kwargs["aws_secret_access_key"] = secret_access_key
        
        self.s3_client = boto3.client("s3", **client_kwargs)
    
    def upload_blob(
        self,
        container: str,
        blob_name: str,
        data: bytes | BinaryIO,
        content_type: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> str:
        """Upload blob to S3-compatible storage"""
        try:
            # Create container/bucket if it doesn't exist
            self.create_container_if_not_exists(container)
            
            # Convert bytes to file-like if needed
            if isinstance(data, bytes):
                from io import BytesIO
                data = BytesIO(data)
            
            # Prepare upload parameters
            upload_kwargs = {
                "Bucket": container,
                "Key": blob_name,
                "Body": data,
            }
            
            if content_type:
                upload_kwargs["ContentType"] = content_type
            
            if metadata:
                upload_kwargs["Metadata"] = {
                    k: str(v) for k, v in metadata.items()
                }
            
            self.s3_client.put_object(**upload_kwargs)
            
            # Return URL/path
            if self.endpoint_url:
                return f"{self.endpoint_url}/{container}/{blob_name}"
            else:
                return f"s3://{container}/{blob_name}"
                
        except ClientError as e:
            raise StorageError(f"Failed to upload blob {blob_name}: {e}") from e
        except Exception as e:
            raise StorageError(f"Unexpected error uploading blob {blob_name}: {e}") from e
    
    def download_blob(
        self,
        container: str,
        blob_name: str,
    ) -> bytes:
        """Download blob from S3-compatible storage"""
        try:
            response = self.s3_client.get_object(Bucket=container, Key=blob_name)
            return response["Body"].read()
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                raise BlobNotFoundError(f"Blob {blob_name} not found in container {container}") from e
            raise StorageError(f"Failed to download blob {blob_name}: {e}") from e
        except Exception as e:
            raise StorageError(f"Unexpected error downloading blob {blob_name}: {e}") from e
    
    def delete_blob(
        self,
        container: str,
        blob_name: str,
    ) -> None:
        """Delete blob from S3-compatible storage"""
        try:
            self.s3_client.delete_object(Bucket=container, Key=blob_name)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                raise BlobNotFoundError(f"Blob {blob_name} not found in container {container}") from e
            raise StorageError(f"Failed to delete blob {blob_name}: {e}") from e
        except Exception as e:
            raise StorageError(f"Unexpected error deleting blob {blob_name}: {e}") from e
    
    def blob_exists(
        self,
        container: str,
        blob_name: str,
    ) -> bool:
        """Check if blob exists in S3-compatible storage"""
        try:
            self.s3_client.head_object(Bucket=container, Key=blob_name)
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "404" or error_code == "NoSuchKey":
                return False
            raise StorageError(f"Failed to check blob existence {blob_name}: {e}") from e
        except Exception as e:
            raise StorageError(f"Unexpected error checking blob existence {blob_name}: {e}") from e
    
    def list_blobs(
        self,
        container: str,
        prefix: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> list[str]:
        """List blobs in S3-compatible storage"""
        try:
            list_kwargs = {"Bucket": container}
            if prefix:
                list_kwargs["Prefix"] = prefix
            if max_results:
                list_kwargs["MaxKeys"] = max_results
            
            response = self.s3_client.list_objects_v2(**list_kwargs)
            
            if "Contents" not in response:
                return []
            
            return [obj["Key"] for obj in response["Contents"]]
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchBucket":
                raise ContainerNotFoundError(f"Container {container} not found") from e
            raise StorageError(f"Failed to list blobs in container {container}: {e}") from e
        except Exception as e:
            raise StorageError(f"Unexpected error listing blobs: {e}") from e
    
    def generate_signed_url(
        self,
        container: str,
        blob_name: str,
        expiration_seconds: int = 3600,
    ) -> str:
        """Generate signed URL for temporary access"""
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": container, "Key": blob_name},
                ExpiresIn=expiration_seconds,
            )
            return url
        except ClientError as e:
            raise StorageError(f"Failed to generate signed URL for {blob_name}: {e}") from e
        except Exception as e:
            raise StorageError(f"Unexpected error generating signed URL: {e}") from e
    
    def create_container_if_not_exists(
        self,
        container: str,
    ) -> None:
        """Create S3 bucket if it doesn't exist"""
        try:
            # Check if bucket exists
            try:
                self.s3_client.head_bucket(Bucket=container)
                return  # Bucket exists
            except ClientError:
                pass  # Bucket doesn't exist, create it
            
            # Create bucket
            create_kwargs = {"Bucket": container}
            
            # For MinIO/local, LocationConstraint is not needed
            if not self.endpoint_url:
                # AWS S3 - may need region-specific configuration
                pass
            
            self.s3_client.create_bucket(**create_kwargs)
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "BucketAlreadyExists" or error_code == "BucketAlreadyOwnedByYou":
                return  # Bucket exists, that's fine
            raise StorageError(f"Failed to create container {container}: {e}") from e
        except Exception as e:
            raise StorageError(f"Unexpected error creating container {container}: {e}") from e

