"""No-op blob storage client for DB-only / local setups (no S3 or object storage)."""
from typing import BinaryIO, Optional

from uepi_common.storage.interface import BlobStorageClient


class NoOpBlobStorageClient(BlobStorageClient):
    """
    No-op implementation for environments that use only the database.
    All operations are no-ops; upload returns a placeholder path so callers don't fail.
    Use when object storage (S3/MinIO/Azure) is not configured (e.g. local development).
    """

    def upload_blob(
        self,
        container: str,
        blob_name: str,
        data: bytes | BinaryIO,
        content_type: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> str:
        # Return a placeholder path; results are stored in DB only
        return f"db-only://{container}/{blob_name}"

    def download_blob(self, container: str, blob_name: str) -> bytes:
        return b""

    def delete_blob(self, container: str, blob_name: str) -> None:
        pass

    def blob_exists(self, container: str, blob_name: str) -> bool:
        return False

    def list_blobs(
        self,
        container: str,
        prefix: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> list[str]:
        return []

    def generate_signed_url(
        self,
        container: str,
        blob_name: str,
        expiration_seconds: int = 3600,
    ) -> str:
        return f"db-only://{container}/{blob_name}"

    def create_container_if_not_exists(self, container: str) -> None:
        pass
