"""
Pipeline Engine
Executes metadata-driven ingestion pipelines with mapping, deduplication, and append mode
"""
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID
from datetime import datetime
from pathlib import Path
import pandas as pd
import polars as pl
import hashlib
import json
import os

from uepi_common.ingestion.pipeline_metadata import (
    PipelineMetadata,
    PipelineMode,
    DeduplicationStrategy,
    FieldMapping,
)
from uepi_common.ingestion.format_detector import FormatDetector
from uepi_common.ingestion.data_quality import DataQualityEngine, QualityReport
from uepi_common.ingestion.monitoring import MonitoringService, AlertSeverity
from uepi_common.data_contracts.canonical_base import CanonicalBase


class PipelineEngine:
    """Executes metadata-driven ingestion pipelines"""
    
    def __init__(
        self,
        tenant_id: UUID,
        pipeline_metadata: PipelineMetadata,
        monitoring_service: Optional[MonitoringService] = None,
    ):
        """
        Initialize pipeline engine
        
        Args:
            tenant_id: Tenant identifier
            pipeline_metadata: Pipeline metadata definition
            monitoring_service: Optional monitoring service for metrics and alerts
        """
        self.tenant_id = tenant_id
        self.pipeline = pipeline_metadata
        self.format_detector = FormatDetector()
        self.monitoring = monitoring_service or MonitoringService()
        self.quality_engine = DataQualityEngine(
            required_fields=pipeline_metadata.required_fields,
            validation_rules=pipeline_metadata.validation_rules or {},
        )
    
    def execute(
        self,
        source_file_path: str | Path,
        output_path: Optional[str | Path] = None,
        run_id: Optional[UUID] = None,
        source_file_id_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute the pipeline with data quality and monitoring
        
        Args:
            source_file_path: Path to source data file (can be temp file)
            output_path: Optional output path for processed data (consolidated file path, not timestamped)
            run_id: Optional run identifier for tracking
            source_file_id_override: Optional original filename to use for source_file_id (if source_file_path is a temp file)
            
        Returns:
            Execution result with statistics, quality report, and metrics
        """
        from uuid import uuid4
        
        run_id = run_id or uuid4()
        start_time = datetime.utcnow()
        source_file_path = Path(source_file_path)
        
        try:
            # 1. Load source data (use actual file path for loading)
            actual_file_path = source_file_path
            # If source_file_path doesn't exist but we have override, try to find the actual file
            # For now, just use the path as-is since it should exist
            source_df = self._load_source_data(actual_file_path)
            file_size_mb = os.path.getsize(actual_file_path) / (1024 * 1024) if actual_file_path.exists() else None
            
            # Extract source file identifier (use override if provided, otherwise use filename stem)
            source_file_id = source_file_id_override or source_file_path.stem  # filename without extension
            
            # 2. Apply field mappings
            mapped_df = self._apply_mappings(source_df)
            
            # 3. Add control fields with source file identifier
            mapped_df = self._add_control_fields(mapped_df, source_file_id=source_file_id)
            
            # 4. Data Quality Validation
            quality_report = self.quality_engine.validate(
                mapped_df,
                dataset_id=str(self.pipeline.pipeline_id),
                target_schema=self.pipeline.source_schema,
            )
            
            # Create alerts for quality issues
            error_issues = [issue for issue in quality_report.issues if issue.severity.value == "ERROR"]
            warning_issues = [issue for issue in quality_report.issues if issue.severity.value == "WARNING"]
            
            if error_issues:
                self.monitoring.create_alert(
                    pipeline_id=self.pipeline.pipeline_id,
                    severity=AlertSeverity.HIGH,
                    alert_type="DATA_QUALITY_ERROR",
                    message=f"Data quality validation found {len(error_issues)} error(s)",
                    run_id=run_id,
                    details={"error_count": len(error_issues), "quality_score": quality_report.quality_score},
                )
            
            if warning_issues:
                self.monitoring.create_alert(
                    pipeline_id=self.pipeline.pipeline_id,
                    severity=AlertSeverity.MEDIUM,
                    alert_type="DATA_QUALITY_WARNING",
                    message=f"Data quality validation found {len(warning_issues)} warning(s)",
                    run_id=run_id,
                    details={"warning_count": len(warning_issues)},
                )
            
            # Check if we should continue based on quality and pipeline settings
            if error_issues and not self.pipeline.continue_on_error:
                end_time = datetime.utcnow()
                self.monitoring.record_metrics(
                    pipeline_id=self.pipeline.pipeline_id,
                    run_id=run_id,
                    start_time=start_time,
                    records_processed=len(source_df),
                    error_count=len(error_issues),
                    warning_count=len(warning_issues),
                    end_time=end_time,
                    data_size_mb=file_size_mb,
                )
                
                # Convert numpy/pandas types to native Python types
                def convert_to_native(obj):
                    """Convert numpy/pandas types to native Python types"""
                    import numpy as np
                    import pandas as pd
                    from datetime import datetime, date
                    from uuid import UUID
                    
                    if isinstance(obj, (np.integer, np.int64, np.int32)):
                        return int(obj)
                    elif isinstance(obj, (np.floating, np.float64, np.float32)):
                        return float(obj)
                    elif isinstance(obj, np.bool_):
                        return bool(obj)
                    elif isinstance(obj, (pd.Timestamp, datetime)):
                        return obj.isoformat() if hasattr(obj, 'isoformat') else str(obj)
                    elif isinstance(obj, date):
                        return obj.isoformat()
                    elif isinstance(obj, UUID):
                        return str(obj)
                    elif isinstance(obj, dict):
                        return {k: convert_to_native(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [convert_to_native(item) for item in obj]
                    elif hasattr(obj, 'model_dump'):
                        return convert_to_native(obj.model_dump())
                    return obj
                
                return {
                    "success": False,
                    "error": "Data quality validation failed",
                    "quality_report": convert_to_native(quality_report.model_dump()) if quality_report else None,
                    "run_id": str(run_id),
                }
            
            # 5. Deduplication (within new data only first)
            if self.pipeline.deduplication.strategy != DeduplicationStrategy.NONE:
                mapped_df, duplicates_in_new = self._deduplicate(mapped_df, source_file_path)
            else:
                duplicates_in_new = 0
            
            # 6. Load existing consolidated data and merge
            if output_path:
                existing_df = self._load_existing_consolidated(output_path)
                
                if existing_df is not None and len(existing_df) > 0:
                    # Merge with existing data
                    if self.pipeline.mode == PipelineMode.REPLACE:
                        # Replace mode: use only new data
                        result_df = mapped_df
                        duplicates = duplicates_in_new
                    elif self.pipeline.mode == PipelineMode.UPSERT:
                        # Upsert mode: update existing or insert new
                        result_df = self._upsert_consolidated(existing_df, mapped_df)
                        # Count duplicates: records in new_df that match existing
                        if self.pipeline.deduplication.strategy != DeduplicationStrategy.NONE:
                            duplicates = self._count_duplicates_against_existing(existing_df, mapped_df)
                        else:
                            duplicates = 0
                    else:
                        # APPEND mode: append new data
                        # Apply deduplication across existing + new data
                        combined_df = pd.concat([existing_df, mapped_df], ignore_index=True)
                        if self.pipeline.deduplication.strategy != DeduplicationStrategy.NONE:
                            initial_combined_count = len(combined_df)
                            result_df, _ = self._deduplicate(combined_df, source_file_path)
                            duplicates_total = initial_combined_count - len(result_df)
                            # Only count duplicates from new data (not existing duplicates)
                            duplicates = max(0, duplicates_total - duplicates_in_new)
                        else:
                            result_df = combined_df
                            duplicates = duplicates_in_new
                else:
                    # No existing data, use new data as-is
                    result_df = mapped_df
                    duplicates = duplicates_in_new
            else:
                result_df = mapped_df
                duplicates = duplicates_in_new
            
            # 7. Save consolidated output
            if output_path:
                self._save_consolidated_output(result_df, output_path)
            
            end_time = datetime.utcnow()
            
            # 8. Record metrics
            metrics = self.monitoring.record_metrics(
                pipeline_id=self.pipeline.pipeline_id,
                run_id=run_id,
                start_time=start_time,
                records_processed=len(source_df),
                error_count=len(error_issues),
                warning_count=len(warning_issues),
                end_time=end_time,
                data_size_mb=file_size_mb,
            )
            
            # 9. Return execution result
            # Convert numpy/pandas types to native Python types for JSON serialization
            def convert_to_native(obj):
                """Convert numpy/pandas types to native Python types"""
                import numpy as np
                import pandas as pd
                from datetime import datetime, date
                from uuid import UUID
                
                if isinstance(obj, (np.integer, np.int64, np.int32)):
                    return int(obj)
                elif isinstance(obj, (np.floating, np.float64, np.float32)):
                    return float(obj)
                elif isinstance(obj, np.bool_):
                    return bool(obj)
                elif isinstance(obj, (pd.Timestamp, datetime)):
                    return obj.isoformat() if hasattr(obj, 'isoformat') else str(obj)
                elif isinstance(obj, date):
                    return obj.isoformat()
                elif isinstance(obj, UUID):
                    return str(obj)
                elif isinstance(obj, dict):
                    return {k: convert_to_native(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_to_native(item) for item in obj]
                elif hasattr(obj, 'model_dump'):
                    return convert_to_native(obj.model_dump())
                return obj
            
            quality_report_dict = None
            if quality_report:
                quality_report_dict = convert_to_native(quality_report.model_dump())
            
            metrics_dict = None
            if metrics:
                metrics_dict = convert_to_native(metrics.model_dump())
            
            return {
                "success": True,
                "run_id": str(run_id),
                "records_processed": int(len(source_df)),
                "records_succeeded": int(len(result_df)),
                "records_failed": int(len(error_issues)),
                "records_duplicated": int(duplicates),
                "output_uri": str(output_path) if output_path else None,
                "quality_report": quality_report_dict,
                "metrics": metrics_dict,
                "duration_seconds": float(metrics.duration_seconds) if metrics else None,
            }
        
        except Exception as e:
            end_time = datetime.utcnow()
            
            # Record failed metrics
            self.monitoring.record_metrics(
                pipeline_id=self.pipeline.pipeline_id,
                run_id=run_id,
                start_time=start_time,
                records_processed=0,
                error_count=1,
                end_time=end_time,
            )
            
            # Create critical alert
            self.monitoring.create_alert(
                pipeline_id=self.pipeline.pipeline_id,
                severity=AlertSeverity.CRITICAL,
                alert_type="PIPELINE_EXECUTION_ERROR",
                message=f"Pipeline execution failed: {str(e)}",
                run_id=run_id,
                details={"error": str(e), "error_type": type(e).__name__},
            )
            
            raise
    
    def _load_source_data(self, file_path: str | Path) -> pd.DataFrame:
        """Load source data file"""
        detected_format = self.format_detector.detect_format(file_path)
        return self.format_detector.parse_file(file_path, format=detected_format)
    
    def _apply_mappings(self, source_df: pd.DataFrame) -> pd.DataFrame:
        """Apply field mappings from source to target"""
        mapped_df = pd.DataFrame()
        
        for mapping in self.pipeline.field_mappings:
            source_field = mapping.source_field
            target_field = mapping.target_field
            transform_func = mapping.transform_function
            default_value = mapping.default_value
            
            if source_field in source_df.columns:
                series = source_df[source_field]
                
                # Apply transformations
                if transform_func == 'to_date':
                    series = pd.to_datetime(series, errors='coerce').dt.date
                elif transform_func == 'to_datetime':
                    series = pd.to_datetime(series, errors='coerce')
                elif transform_func == 'to_float':
                    series = pd.to_numeric(series, errors='coerce')
                elif transform_func == 'to_int':
                    series = pd.to_numeric(series, errors='coerce').astype('Int64')
                elif transform_func == 'to_bool':
                    series = series.astype(str).str.lower().map({
                        'true': True, 'false': False, '1': True, '0': False,
                        'yes': True, 'no': False, 'y': True, 'n': False
                    })
                elif transform_func == 'normalize_string':
                    series = series.astype(str).str.strip().str.upper()
                elif transform_func == 'lowercase':
                    series = series.astype(str).str.lower()
                elif transform_func == 'uppercase':
                    series = series.astype(str).str.upper()
                
                mapped_df[target_field] = series
            elif default_value is not None:
                mapped_df[target_field] = default_value
            elif mapping.required:
                # Required field missing - will be caught in validation
                mapped_df[target_field] = None
            else:
                mapped_df[target_field] = None
        
        return mapped_df
    
    def _add_control_fields(self, df: pd.DataFrame, source_file_id: Optional[str] = None) -> pd.DataFrame:
        """Add control fields to target data"""
        control_fields = self.pipeline.control_fields or {}
        now = datetime.utcnow()
        
        # Add canonical base fields
        df['tenant_id'] = str(self.tenant_id)
        df['source_system'] = self.pipeline.source_type
        # Use actual source file identifier if provided, otherwise fallback to pipeline ID
        df['source_file_id'] = source_file_id or f"pipeline_{self.pipeline.pipeline_id}"
        df['ingestion_id'] = str(self.pipeline.pipeline_id)
        
        # Add control fields from metadata with defaults
        if 'created_at' in control_fields:
            if control_fields['created_at'] == 'CURRENT_TIMESTAMP':
                df['created_at'] = now
            else:
                df['created_at'] = control_fields['created_at']
        else:
            df['created_at'] = now
        
        if 'updated_at' in control_fields:
            if control_fields['updated_at'] == 'CURRENT_TIMESTAMP':
                df['updated_at'] = now
            else:
                df['updated_at'] = control_fields['updated_at']
        else:
            df['updated_at'] = now
        
        if 'active_flag' in control_fields:
            df['active_flag'] = control_fields['active_flag']
        else:
            df['active_flag'] = True  # Default to active
        
        if 'effective_date' in control_fields and control_fields['effective_date']:
            if control_fields['effective_date'] == 'CURRENT_TIMESTAMP':
                df['effective_date'] = now
            else:
                df['effective_date'] = pd.to_datetime(control_fields['effective_date'], errors='coerce')
        else:
            # Default effective_date to current timestamp (record is effective from creation)
            df['effective_date'] = now
        
        if 'expiration_date' in control_fields and control_fields['expiration_date']:
            df['expiration_date'] = pd.to_datetime(control_fields['expiration_date'], errors='coerce')
        else:
            df['expiration_date'] = None
        
        # Compute record hash for idempotency (exclude control fields from hash)
        df['record_hash'] = df.apply(self._compute_record_hash, axis=1)
        
        return df
    
    def _compute_record_hash(self, row: pd.Series) -> str:
        """Compute hash of record content (excluding metadata fields)"""
        # Exclude metadata fields
        exclude_fields = {
            'tenant_id', 'source_system', 'source_file_id', 'ingestion_id',
            'created_at', 'updated_at', 'record_hash'
        }
        
        data = {k: v for k, v in row.items() if k not in exclude_fields}
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate mapped data"""
        errors = []
        error_count = 0
        
        # Check required fields
        for field in self.pipeline.required_fields:
            if field not in df.columns:
                errors.append({
                    "field": field,
                    "error": f"Required field missing: {field}",
                })
                error_count += 1
            elif df[field].isna().any():
                missing_count = df[field].isna().sum()
                errors.append({
                    "field": field,
                    "error": f"Required field has {missing_count} null values",
                    "count": missing_count,
                })
                error_count += missing_count
        
        # Apply validation rules if provided
        if self.pipeline.validation_rules:
            for rule_name, rule_config in self.pipeline.validation_rules.items():
                # Custom validation logic can be added here
                pass
        
        return {
            "valid": error_count == 0,
            "error_count": error_count,
            "errors": errors,
        }
    
    def _deduplicate(
        self,
        df: pd.DataFrame,
        source_file_path: str | Path,
    ) -> tuple[pd.DataFrame, int]:
        """Deduplicate records based on strategy"""
        strategy = self.pipeline.deduplication.strategy
        duplicates = 0
        
        if strategy == DeduplicationStrategy.HASH:
            # Use record_hash for deduplication
            if 'record_hash' in df.columns:
                initial_count = len(df)
                df = df.drop_duplicates(subset=['record_hash'], keep='first')
                duplicates = initial_count - len(df)
        
        elif strategy == DeduplicationStrategy.KEY_FIELDS:
            # Use specified key fields
            key_fields = self.pipeline.deduplication.key_fields or []
            if key_fields and all(f in df.columns for f in key_fields):
                initial_count = len(df)
                df = df.drop_duplicates(subset=key_fields, keep='first')
                duplicates = initial_count - len(df)
        
        elif strategy == DeduplicationStrategy.SOURCE_ID:
            # Use source ID field
            source_id_field = self.pipeline.deduplication.source_id_field
            if source_id_field and source_id_field in df.columns:
                initial_count = len(df)
                df = df.drop_duplicates(subset=[source_id_field], keep='first')
                duplicates = initial_count - len(df)
        
        return df, duplicates
    
    def _count_duplicates_against_existing(self, existing_df: pd.DataFrame, new_df: pd.DataFrame) -> int:
        """Count how many records in new_df are duplicates of existing_df"""
        strategy = self.pipeline.deduplication.strategy
        
        if strategy == DeduplicationStrategy.HASH and 'record_hash' in existing_df.columns and 'record_hash' in new_df.columns:
            existing_hashes = set(existing_df['record_hash'].dropna())
            new_hashes = set(new_df['record_hash'].dropna())
            return len(new_hashes & existing_hashes)
        
        elif strategy == DeduplicationStrategy.KEY_FIELDS:
            key_fields = self.pipeline.deduplication.key_fields or []
            if key_fields and all(f in existing_df.columns and f in new_df.columns for f in key_fields):
                existing_keys = set(tuple(row) for row in existing_df[key_fields].dropna().itertuples(index=False))
                new_keys = set(tuple(row) for row in new_df[key_fields].dropna().itertuples(index=False))
                return len(new_keys & existing_keys)
        
        elif strategy == DeduplicationStrategy.SOURCE_ID:
            source_id_field = self.pipeline.deduplication.source_id_field
            if source_id_field and source_id_field in existing_df.columns and source_id_field in new_df.columns:
                existing_ids = set(existing_df[source_id_field].dropna())
                new_ids = set(new_df[source_id_field].dropna())
                return len(new_ids & existing_ids)
        
        return 0
    
    def _load_existing_consolidated(self, output_path: str | Path) -> Optional[pd.DataFrame]:
        """Load existing consolidated file if it exists"""
        output_path = Path(output_path)
        if not output_path.is_absolute():
            output_path = output_path.resolve()
        
        # Try both parquet and CSV versions (since we might save as CSV if parquet not available)
        parquet_path = output_path.with_suffix('.parquet')
        csv_path = output_path.with_suffix('.csv')
        
        # Check which file actually exists
        actual_path = None
        if parquet_path.exists():
            actual_path = parquet_path
        elif csv_path.exists():
            actual_path = csv_path
        else:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"No existing consolidated file found at {output_path} (checked {parquet_path} and {csv_path})")
            return None
        
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Loading existing consolidated file: {actual_path}")
            if actual_path.suffix == '.parquet':
                df = pd.read_parquet(actual_path)
                logger.info(f"Loaded {len(df)} records from parquet file")
                return df
            elif actual_path.suffix == '.csv':
                df = pd.read_csv(actual_path)
                logger.info(f"Loaded {len(df)} records from CSV file")
                return df
            return None
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error loading existing consolidated file {actual_path}: {e}", exc_info=True)
            return None
    
    def _upsert_consolidated(self, existing_df: pd.DataFrame, new_df: pd.DataFrame) -> pd.DataFrame:
        """Upsert records: update existing records or insert new ones"""
        strategy = self.pipeline.deduplication.strategy
        
        if strategy == DeduplicationStrategy.KEY_FIELDS:
            key_fields = self.pipeline.deduplication.key_fields or []
            if key_fields and all(f in existing_df.columns and f in new_df.columns for f in key_fields):
                # Set index on key fields for both dataframes
                existing_indexed = existing_df.set_index(key_fields)
                new_indexed = new_df.set_index(key_fields)
                # Update existing with new values, add new records
                existing_indexed.update(new_indexed)
                # Add new records that don't exist in existing
                new_only = new_indexed[~new_indexed.index.isin(existing_indexed.index)]
                result = pd.concat([existing_indexed, new_only])
                return result.reset_index()
        
        elif strategy == DeduplicationStrategy.SOURCE_ID:
            source_id_field = self.pipeline.deduplication.source_id_field
            if source_id_field and source_id_field in existing_df.columns and source_id_field in new_df.columns:
                # Set index on source_id for both dataframes
                existing_indexed = existing_df.set_index(source_id_field)
                new_indexed = new_df.set_index(source_id_field)
                # Update existing with new values, add new records
                existing_indexed.update(new_indexed)
                # Add new records that don't exist in existing
                new_only = new_indexed[~new_indexed.index.isin(existing_indexed.index)]
                result = pd.concat([existing_indexed, new_only])
                return result.reset_index()
        
        # Default: append with deduplication by hash
        combined = pd.concat([existing_df, new_df], ignore_index=True)
        if strategy == DeduplicationStrategy.HASH and 'record_hash' in combined.columns:
            # Keep last (newest) record for each hash
            combined = combined.drop_duplicates(subset=['record_hash'], keep='last')
        return combined
    
    def _save_consolidated_output(self, df: pd.DataFrame, output_path: str | Path) -> None:
        """Save consolidated data to output path (one file per entity)"""
        output_path = Path(output_path)
        # Ensure absolute path
        if not output_path.is_absolute():
            output_path = output_path.resolve()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Update updated_at for all records
        now = datetime.utcnow()
        if 'updated_at' in df.columns:
            df['updated_at'] = now
        
        # Determine which format to use based on what already exists or requested format
        parquet_path = output_path.with_suffix('.parquet')
        csv_path = output_path.with_suffix('.csv')
        
        # If parquet file exists, use parquet; if CSV exists, use CSV; otherwise try parquet first
        use_parquet = False
        if parquet_path.exists():
            use_parquet = True
            save_path = parquet_path
        elif csv_path.exists():
            use_parquet = False
            save_path = csv_path
        elif output_path.suffix == '.parquet':
            use_parquet = True
            save_path = parquet_path
        else:
            use_parquet = False
            save_path = csv_path
        
        try:
            if use_parquet:
                df.to_parquet(save_path, index=False)
            else:
                df.to_csv(save_path, index=False)
        except ImportError as e:
            # If parquet engine not available, fallback to CSV
            if 'parquet' in str(e).lower() or 'pyarrow' in str(e).lower():
                csv_path = output_path.with_suffix('.csv')
                df.to_csv(csv_path, index=False)
            else:
                raise
        except Exception as e:
            # Log error for debugging
            import logging
            logging.getLogger(__name__).error(f"Error saving consolidated output to {save_path}: {e}")
            raise

