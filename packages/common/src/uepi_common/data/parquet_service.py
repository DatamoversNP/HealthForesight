"""Parquet data service - handles Parquet file operations with data zone organization"""
from enum import Enum
from typing import Any, Optional
from uuid import UUID
import tempfile
import os
import io
from pathlib import Path

import polars as pl

from uepi_common.storage.interface import BlobStorageClient
from uepi_common.storage.factory import create_storage_client


class DataZone(str, Enum):
    """Data zones for organizing analytical datasets"""
    RAW = "raw"  # Immutable original uploads
    CURATED = "curated"  # Normalized Parquet partitions
    RESULTS = "results"  # Analysis outputs (Parquet + summary.json)
    EXPORTS = "exports"  # PDFs, PPTX, other exports


class ParquetDataService:
    """Service for managing Parquet files in object storage with proper partitioning
    
    This service handles:
    - Writing Parquet files to appropriate data zones
    - Partitioning by date/lob/market
    - Reading partitioned Parquet files efficiently
    - Maintaining data lineage
    """
    
    def __init__(
        self,
        storage_client: Optional[BlobStorageClient] = None,
        container: str = "uepi-data",
    ):
        """Initialize Parquet data service
        
        Args:
            storage_client: BlobStorageClient instance (if None, will use factory)
            container: Container/bucket name
        """
        self.storage_client = storage_client or create_storage_client()
        self.container = container
    
    def write_partitioned_dataframe(
        self,
        df: pl.DataFrame,
        tenant_id: UUID,
        dataset_type: str,
        zone: DataZone,
        partition_by: list[str],
        partition_values: dict[str, str],
        schema_version: str = "1.0",
    ) -> str:
        """Write DataFrame to Parquet with partitioning
        
        Args:
            df: Polars DataFrame to write
            tenant_id: Tenant ID for multi-tenancy
            dataset_type: Dataset type (e.g., 'claims_lines', 'enrollment')
            zone: Data zone (RAW, CURATED, RESULTS, EXPORTS)
            partition_by: Partition columns (e.g., ['year', 'month', 'lob', 'market'])
            partition_values: Partition values (e.g., {'year': '2024', 'month': '01', 'lob': 'Commercial', 'market': 'CA'})
            schema_version: Schema version for lineage tracking
            
        Returns:
            Blob path/URI of the written Parquet file
        """
        # Build partition path
        partition_path_parts = [zone.value, dataset_type]
        for col in partition_by:
            if col not in partition_values:
                raise ValueError(f"Missing partition value for column: {col}")
            partition_path_parts.append(f"{col}={partition_values[col]}")
        
        partition_path = "/".join(partition_path_parts)
        blob_name = f"{tenant_id}/{partition_path}/data.parquet"
        
        # Write to temporary file first
        with tempfile.NamedTemporaryFile(delete=False, suffix=".parquet") as tmp:
            df.write_parquet(tmp.name, compression="snappy")
            tmp_path = tmp.name
        
        try:
            # Upload to storage
            with open(tmp_path, "rb") as f:
                self.storage_client.upload_blob(
                    container=self.container,
                    blob_name=blob_name,
                    data=f,
                    content_type="application/parquet",
                    metadata={
                        "schema_version": schema_version,
                        "dataset_type": dataset_type,
                        "zone": zone.value,
                        "tenant_id": str(tenant_id),
                        **{f"partition_{k}": v for k, v in partition_values.items()},
                    },
                )
            
            return blob_name
            
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def read_partitioned_dataframe(
        self,
        tenant_id: UUID,
        dataset_type: str,
        zone: DataZone,
        partition_filters: Optional[dict[str, str]] = None,
        columns: Optional[list[str]] = None,
    ) -> pl.DataFrame:
        """Read Parquet files matching partition filters
        
        Args:
            tenant_id: Tenant ID
            dataset_type: Dataset type
            zone: Data zone
            partition_filters: Optional filters (e.g., {'year': '2024', 'month': '01'})
            columns: Optional list of columns to read (if None, reads all)
            
        Returns:
            Combined Polars DataFrame from all matching partitions
        """
        # Build prefix to list matching partitions
        prefix_parts = [str(tenant_id), zone.value, dataset_type]
        if partition_filters:
            for key, value in sorted(partition_filters.items()):
                prefix_parts.append(f"{key}={value}")
        
        prefix = "/".join(prefix_parts) + "/"
        
        # List all matching blobs
        blob_names = self.storage_client.list_blobs(
            container=self.container,
            prefix=prefix,
        )
        
        if not blob_names:
            # Return empty DataFrame with expected schema if available
            # TODO: Load schema from metadata if needed
            return pl.DataFrame()
        
        # Download and read each Parquet file
        dfs = []
        for blob_name in blob_names:
            if not blob_name.endswith(".parquet"):
                continue
            
            try:
                # Download blob
                parquet_bytes = self.storage_client.download_blob(
                    container=self.container,
                    blob_name=blob_name,
                )
                
                # Read into DataFrame
                df = pl.read_parquet(io.BytesIO(parquet_bytes))
                
                # Select columns if specified
                if columns:
                    # Only select columns that exist
                    existing_cols = [c for c in columns if c in df.columns]
                    if existing_cols:
                        df = df.select(existing_cols)
                
                dfs.append(df)
                
            except Exception as e:
                # Log error but continue with other partitions
                # TODO: Add proper logging
                print(f"Error reading partition {blob_name}: {e}")
                continue
        
        if not dfs:
            return pl.DataFrame()
        
        # Concatenate all DataFrames
        return pl.concat(dfs)
    
    def list_partitions(
        self,
        tenant_id: UUID,
        dataset_type: str,
        zone: DataZone,
    ) -> list[dict[str, str]]:
        """List available partitions for a dataset
        
        Args:
            tenant_id: Tenant ID
            dataset_type: Dataset type
            zone: Data zone
            
        Returns:
            List of partition dictionaries (e.g., [{'year': '2024', 'month': '01', 'lob': 'Commercial'}])
        """
        prefix = f"{tenant_id}/{zone.value}/{dataset_type}/"
        
        blob_names = self.storage_client.list_blobs(
            container=self.container,
            prefix=prefix,
        )
        
        # Extract unique partition combinations
        partitions = set()
        for blob_name in blob_names:
            # Extract partition path (e.g., "year=2024/month=01/lob=Commercial/market=CA")
            relative_path = blob_name.replace(prefix, "")
            if "/data.parquet" in relative_path:
                partition_path = relative_path.replace("/data.parquet", "")
                partitions.add(partition_path)
        
        # Parse partition paths into dicts
        partition_dicts = []
        for partition_path in partitions:
            partition_dict = {}
            for part in partition_path.split("/"):
                if "=" in part:
                    key, value = part.split("=", 1)
                    partition_dict[key] = value
            if partition_dict:
                partition_dicts.append(partition_dict)
        
        return partition_dicts
    
    def delete_partition(
        self,
        tenant_id: UUID,
        dataset_type: str,
        zone: DataZone,
        partition_values: dict[str, str],
    ) -> None:
        """Delete a specific partition
        
        Args:
            tenant_id: Tenant ID
            dataset_type: Dataset type
            zone: Data zone
            partition_values: Partition values identifying the partition to delete
        """
        # Build partition path
        partition_path_parts = [zone.value, dataset_type]
        for key, value in sorted(partition_values.items()):
            partition_path_parts.append(f"{key}={value}")
        
        partition_path = "/".join(partition_path_parts)
        blob_name = f"{tenant_id}/{partition_path}/data.parquet"
        
        # Delete blob
        try:
            self.storage_client.delete_blob(
                container=self.container,
                blob_name=blob_name,
            )
        except Exception as e:
            # Log error
            print(f"Error deleting partition {blob_name}: {e}")
            raise



