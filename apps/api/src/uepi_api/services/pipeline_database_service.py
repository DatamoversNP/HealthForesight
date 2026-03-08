"""Service layer for pipeline execution with database storage"""
from typing import Dict, Any, Optional, List
from uuid import UUID
from pathlib import Path
from datetime import datetime
import pandas as pd

from sqlalchemy.orm import Session
from uepi_common.ingestion.pipeline_engine import PipelineEngine
from uepi_common.ingestion.pipeline_metadata import PipelineMetadata
from uepi_api.repositories.canonical_data import CanonicalDataRepository


class PipelineDatabaseService:
    """Service for executing pipelines with database storage"""
    
    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.repository = CanonicalDataRepository(db)
    
    def execute_pipeline_to_database(
        self,
        pipeline_metadata: PipelineMetadata,
        source_file_path: str | Path,
        source_file_id: str,
        ingestion_id: UUID,
        source_system: str = "PIPELINE",
    ) -> Dict[str, Any]:
        """
        Execute pipeline and write results to database instead of files
        
        Returns execution result with statistics
        """
        from uepi_common.ingestion.monitoring import MonitoringService
        
        # Create pipeline engine (but we'll intercept the save step)
        monitoring_service = MonitoringService()
        engine = PipelineEngine(self.tenant_id, pipeline_metadata, monitoring_service)
        
        # Execute pipeline but intercept before file save
        # We'll manually process the result_df and save to database
        start_time = datetime.utcnow()
        
        try:
            # 1. Load source data
            source_df = engine._load_source_data(source_file_path)
            file_size_mb = Path(source_file_path).stat().st_size / (1024 * 1024) if Path(source_file_path).exists() else None
            
            # 2. Apply mappings
            mapped_df = engine._apply_mappings(source_df)
            
            # 3. Add control fields
            mapped_df = engine._add_control_fields(mapped_df, source_file_id=source_file_id)
            
            # 4. Data quality validation
            quality_report = engine.quality_engine.validate(
                mapped_df,
                dataset_id=str(pipeline_metadata.pipeline_id),
                target_schema=pipeline_metadata.source_schema,
            )
            
            error_issues = [issue for issue in quality_report.issues if issue.severity.value == "ERROR"]
            warning_issues = [issue for issue in quality_report.issues if issue.severity.value == "WARNING"]
            
            if error_issues and not pipeline_metadata.continue_on_error:
                return {
                    "success": False,
                    "error": "Data quality validation failed",
                    "quality_report": quality_report.model_dump() if quality_report else None,
                }
            
            # 5. Deduplication (within new data)
            from uepi_common.ingestion.pipeline_metadata import DeduplicationStrategy
            if pipeline_metadata.deduplication.strategy != DeduplicationStrategy.NONE:
                mapped_df, duplicates_in_new = engine._deduplicate(mapped_df, source_file_path)
            else:
                duplicates_in_new = 0
            
            # 6. Load existing data from database and merge
            existing_df = self._load_existing_from_database(pipeline_metadata.target_dataset_type)
            
            if existing_df is not None and len(existing_df) > 0:
                # Merge with existing data based on mode
                from uepi_common.ingestion.pipeline_metadata import PipelineMode
                if pipeline_metadata.mode == PipelineMode.REPLACE:
                    result_df = mapped_df
                    duplicates = duplicates_in_new
                elif pipeline_metadata.mode == PipelineMode.UPSERT:
                    result_df = engine._upsert_consolidated(existing_df, mapped_df)
                    if pipeline_metadata.deduplication.strategy != DeduplicationStrategy.NONE:
                        duplicates = engine._count_duplicates_against_existing(existing_df, mapped_df)
                    else:
                        duplicates = 0
                else:  # APPEND
                    combined_df = pd.concat([existing_df, mapped_df], ignore_index=True)
                    if pipeline_metadata.deduplication.strategy != DeduplicationStrategy.NONE:
                        initial_count = len(combined_df)
                        result_df, _ = engine._deduplicate(combined_df, source_file_path)
                        duplicates_total = initial_count - len(result_df)
                        duplicates = max(0, duplicates_total - duplicates_in_new)
                    else:
                        result_df = combined_df
                        duplicates = duplicates_in_new
            else:
                result_df = mapped_df
                duplicates = duplicates_in_new
            
            # 7. Save to database instead of file
            records_inserted = self._save_to_database(
                result_df,
                pipeline_metadata.target_dataset_type,
                source_system,
                source_file_id,
                ingestion_id,
            )
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            return {
                "success": True,
                "records_processed": int(len(source_df)),
                "records_succeeded": int(len(result_df)),
                "records_inserted": records_inserted,
                "records_failed": int(len(error_issues)),
                "records_duplicated": int(duplicates),
                "quality_report": quality_report.model_dump() if quality_report else None,
                "duration_seconds": duration,
            }
        
        except Exception as e:
            raise
    
    def _load_existing_from_database(self, dataset_type: str) -> Optional[pd.DataFrame]:
        """Load existing data from database based on dataset type"""
        if dataset_type == "CLAIMS_LINES":
            return self.repository.get_claims_lines(self.tenant_id)
        elif dataset_type == "ENROLLMENT" or dataset_type == "ELIGIBILITY_ENROLLMENT":
            return self.repository.get_enrollment_records(self.tenant_id)
        elif dataset_type == "PROVIDERS" or dataset_type == "PROVIDER_MASTER":
            return self.repository.get_provider_records(self.tenant_id)
        else:
            # For other types, return None (no existing data)
            return None
    
    def _save_to_database(
        self,
        df: pd.DataFrame,
        dataset_type: str,
        source_system: str,
        source_file_id: str,
        ingestion_id: UUID,
    ) -> int:
        """Save DataFrame to appropriate database table"""
        # Convert DataFrame to list of dicts
        records = df.to_dict('records')
        
        if dataset_type == "CLAIMS_LINES":
            return self.repository.bulk_insert_claims_lines(
                self.tenant_id,
                records,
                source_system,
                source_file_id,
                ingestion_id,
            )
        elif dataset_type == "ENROLLMENT" or dataset_type == "ELIGIBILITY_ENROLLMENT":
            return self.repository.bulk_insert_enrollment_records(
                self.tenant_id,
                records,
                source_system,
                source_file_id,
                ingestion_id,
            )
        elif dataset_type == "PROVIDERS" or dataset_type == "PROVIDER_MASTER":
            return self.repository.bulk_insert_provider_records(
                self.tenant_id,
                records,
                source_system,
                source_file_id,
                ingestion_id,
            )
        else:
            raise ValueError(f"Unsupported dataset type for database storage: {dataset_type}")

