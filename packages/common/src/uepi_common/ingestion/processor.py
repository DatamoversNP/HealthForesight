"""Ingestion processor - handles raw → curated transformation"""
from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID
import polars as pl

from uepi_common.data.parquet_service import ParquetDataService, DataZone
from uepi_common.ingestion.validator import DataValidator, ValidationResult
from uepi_common.data_contracts.manifest import DatasetType, IngestionMode


class IngestionProcessor:
    """Processes ingested data: validation → raw zone → curated zone"""
    
    def __init__(
        self,
        tenant_id: UUID,
        dataset_type: DatasetType,
        parquet_service: Optional[ParquetDataService] = None,
    ):
        """Initialize ingestion processor
        
        Args:
            tenant_id: Tenant ID for multi-tenancy
            dataset_type: Type of dataset being ingested
            parquet_service: ParquetDataService instance (creates default if None)
        """
        self.tenant_id = tenant_id
        self.dataset_type = dataset_type
        self.validator = DataValidator(dataset_type)
        self.parquet_service = parquet_service or ParquetDataService()
    
    def process_file(
        self,
        file_path: str,
        file_format: str,
        ingestion_mode: IngestionMode = IngestionMode.MANUAL_UPLOAD,
        replace_existing: bool = False,
    ) -> dict[str, Any]:
        """Process a single file: validate → raw zone → curated zone
        
        Args:
            file_path: Path to file (local or blob URI)
            file_format: File format ('parquet', 'csv', 'json')
            ingestion_mode: Ingestion mode
            replace_existing: Whether to replace existing partitions
            
        Returns:
            Dictionary with processing results:
            - validation_result: ValidationResult
            - raw_zone_uri: URI of file in raw zone
            - curated_partitions: List of curated partition URIs
            - errors: List of errors (if any)
        """
        # Step 1: Validate
        validation_result = self.validator.validate_file(file_path, format=file_format, strict=False)
        
        if not validation_result.valid:
            return {
                "success": False,
                "validation_result": validation_result.to_dict(),
                "raw_zone_uri": None,
                "curated_partitions": [],
                "errors": [f"Validation failed: {len(validation_result.errors)} errors"],
            }
        
        # Step 2: Read validated data
        if file_format.lower() == "parquet":
            df = pl.read_parquet(file_path)
        elif file_format.lower() == "csv":
            df = pl.read_csv(file_path)
        elif file_format.lower() == "json":
            df = pl.read_json(file_path)
        else:
            return {
                "success": False,
                "validation_result": validation_result.to_dict(),
                "raw_zone_uri": None,
                "curated_partitions": [],
                "errors": [f"Unsupported format: {file_format}"],
            }
        
        # Step 3: Write to raw zone (immutable original)
        raw_blob_name = self._write_to_raw_zone(df, file_path, file_format)
        
        # Step 4: Transform and write to curated zone (partitioned Parquet)
        curated_partitions = self._write_to_curated_zone(df, replace_existing)
        
        return {
            "success": True,
            "validation_result": validation_result.to_dict(),
            "raw_zone_uri": raw_blob_name,
            "curated_partitions": curated_partitions,
            "record_count": len(df),
            "warnings": validation_result.warnings,
        }
    
    def _write_to_raw_zone(
        self,
        df: pl.DataFrame,
        original_path: str,
        file_format: str,
    ) -> str:
        """Write original file to raw zone (immutable)
        
        Args:
            df: DataFrame to write
            original_path: Original file path (for naming)
            file_format: Original file format
            
        Returns:
            Blob name in raw zone
        """
        # Generate blob name with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        dataset_type_str = self.dataset_type.value.lower()
        filename = f"{dataset_type_str}_{timestamp}.parquet"
        
        blob_name = f"{self.tenant_id}/raw/{dataset_type_str}/{timestamp[:8]}/{filename}"
        
        # Write as Parquet (normalized format)
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".parquet") as tmp:
            df.write_parquet(tmp.name)
            tmp_path = tmp.name
        
        try:
            with open(tmp_path, "rb") as f:
                self.parquet_service.storage_client.upload_blob(
                    container=self.parquet_service.container,
                    blob_name=blob_name,
                    data=f,
                    content_type="application/parquet",
            metadata={
                "original_path": original_path,
                "original_format": file_format,
                "dataset_type": self.dataset_type.value,
                    "tenant_id": str(self.tenant_id),
                    "record_count": str(len(df)),
                },
                )
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
        return blob_name
    
    def _write_to_curated_zone(
        self,
        df: pl.DataFrame,
        replace_existing: bool,
    ) -> list[str]:
        """Write validated data to curated zone (partitioned)
        
        Args:
            df: Validated DataFrame
            replace_existing: Whether to replace existing partitions
            
        Returns:
            List of curated partition blob names
        """
        # Determine partition columns based on dataset type
        partition_by = self._get_partition_columns()
        
        # Group by partition values
        partitions = {}
        
        for row in df.iter_rows(named=True):
            partition_values = self._extract_partition_values(row, partition_by)
            partition_key = "_".join([f"{k}={v}" for k, v in sorted(partition_values.items())])
            
            if partition_key not in partitions:
                partitions[partition_key] = {
                    "values": partition_values,
                    "rows": [],
                }
            
            partitions[partition_key]["rows"].append(row)
        
        # Write each partition
        curated_blob_names = []
        dataset_type_str = self.dataset_type.value.lower()
        
        for partition_key, partition_data in partitions.items():
            partition_df = pl.DataFrame(partition_data["rows"])
            partition_values = partition_data["values"]
            
            # Convert date fields if needed
            for col in partition_df.columns:
                if col in ["service_date", "paid_date", "enrollment_month", "effective_date"]:
                    if partition_df[col].dtype == pl.Utf8:
                        partition_df = partition_df.with_columns(
                            pl.col(col).str.strptime(pl.Date, format="%Y-%m-%d")
                        )
            
            # Determine year/month from date fields
            if "service_date" in partition_df.columns:
                partition_df = partition_df.with_columns(
                    pl.col("service_date").dt.year().alias("year"),
                    pl.col("service_date").dt.month().alias("month"),
                )
                if "year" not in partition_values:
                    partition_values["year"] = str(partition_df["year"][0])
                if "month" not in partition_values:
                    partition_values["month"] = f"{partition_df['month'][0]:02d}"
            
            # Delete existing partition if replace_existing
            if replace_existing:
                try:
                    self.parquet_service.delete_partition(
                        tenant_id=self.tenant_id,
                        dataset_type=dataset_type_str,
                        zone=DataZone.CURATED,
                        partition_values=partition_values,
                    )
                except Exception:
                    pass  # Partition may not exist
            
            # Write partition
            blob_name = self.parquet_service.write_partitioned_dataframe(
                df=partition_df,
                tenant_id=self.tenant_id,
                dataset_type=dataset_type_str,
                zone=DataZone.CURATED,
                partition_by=partition_by,
                partition_values=partition_values,
            )
            
            curated_blob_names.append(blob_name)
        
        return curated_blob_names
    
    def _get_partition_columns(self) -> list[str]:
        """Get partition columns for dataset type"""
        partition_map = {
            DatasetType.CLAIMS_LINES: ["year", "month", "lob", "market"],
            DatasetType.ENROLLMENT: ["year", "month", "lob", "market"],
            DatasetType.PROVIDERS: ["year", "month"],  # Snapshot-based
            DatasetType.BENEFIT_DESIGN: ["year", "lob"],  # Annual
        }
        return partition_map.get(self.dataset_type, ["year", "month"])
    
    def _extract_partition_values(self, row: dict[str, Any], partition_by: list[str]) -> dict[str, str]:
        """Extract partition values from row"""
        partition_values = {}
        
        for col in partition_by:
            if col in row:
                value = row[col]
                if isinstance(value, date):
                    if col == "year":
                        partition_values["year"] = str(value.year)
                    elif col == "month":
                        partition_values["month"] = f"{value.month:02d}"
                    else:
                        partition_values[col] = str(value)
                else:
                    partition_values[col] = str(value)
        
        return partition_values

