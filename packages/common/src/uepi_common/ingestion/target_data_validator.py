"""
Target Data Validation Service
Validates consolidated target data model files after pipeline execution
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID
from pathlib import Path
import pandas as pd
import logging

from uepi_common.ingestion.data_quality import DataQualityEngine, QualityReport, QualityIssue, QualitySeverity, QualityCheckType

logger = logging.getLogger(__name__)


class TargetDataValidator:
    """Validates consolidated target data model files"""
    
    def __init__(self, tenant_id: UUID):
        """
        Initialize target data validator
        
        Args:
            tenant_id: Tenant identifier
        """
        self.tenant_id = tenant_id
        self.quality_engine = DataQualityEngine()
    
    def validate_target_file(
        self,
        target_file_path: Path,
        dataset_type: str,
        required_fields: Optional[List[str]] = None,
        validation_rules: Optional[Dict[str, Any]] = None,
    ) -> QualityReport:
        """
        Validate a consolidated target data file
        
        Args:
            target_file_path: Path to consolidated target data file
            dataset_type: Dataset type identifier
            required_fields: List of required fields
            validation_rules: Custom validation rules
            
        Returns:
            QualityReport with validation results
        """
        if not target_file_path.exists():
            logger.warning(f"Target file does not exist: {target_file_path}")
            return QualityReport(
                dataset_id=dataset_type,
                total_rows=0,
                valid_rows=0,
                invalid_rows=0,
                quality_score=0.0,
                completeness_score=0.0,
                validity_score=0.0,
                uniqueness_score=0.0,
                issues=[QualityIssue(
                    check_type=QualityCheckType.SCHEMA_VALIDATION,
                    severity=QualitySeverity.ERROR,
                    issue_description=f"Target file does not exist: {target_file_path}",
                    affected_rows=0,
                )],
            )
        
        try:
            # Load target data
            if target_file_path.suffix == '.parquet':
                df = pd.read_parquet(target_file_path)
            elif target_file_path.suffix == '.csv':
                df = pd.read_csv(target_file_path)
            else:
                # Try parquet first, then CSV
                parquet_path = target_file_path.with_suffix('.parquet')
                csv_path = target_file_path.with_suffix('.csv')
                if parquet_path.exists():
                    df = pd.read_parquet(parquet_path)
                elif csv_path.exists():
                    df = pd.read_csv(csv_path)
                else:
                    raise FileNotFoundError(f"Target file not found: {target_file_path}")
            
            logger.info(f"Loaded {len(df)} records from {target_file_path}")
            
            # Update quality engine with required fields and rules
            if required_fields:
                self.quality_engine.required_fields = required_fields
            if validation_rules:
                self.quality_engine.validation_rules = validation_rules
            
            # Validate data
            target_schema = {
                "required_fields": required_fields or [],
                "fields": {col: {"type": str(df[col].dtype)} for col in df.columns},
            }
            
            report = self.quality_engine.validate(
                df=df,
                dataset_id=dataset_type,
                target_schema=target_schema,
            )
            
            logger.info(
                f"Validation complete for {dataset_type}: "
                f"quality_score={report.quality_score:.2%}, "
                f"issues={len(report.issues)}"
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Error validating target file {target_file_path}: {e}", exc_info=True)
            return QualityReport(
                dataset_id=dataset_type,
                total_rows=0,
                valid_rows=0,
                invalid_rows=0,
                quality_score=0.0,
                completeness_score=0.0,
                validity_score=0.0,
                uniqueness_score=0.0,
                issues=[QualityIssue(
                    check_type=QualityCheckType.SCHEMA_VALIDATION,
                    severity=QualitySeverity.ERROR,
                    issue_description=f"Error validating target file: {str(e)}",
                    affected_rows=0,
                )],
            )
    
    def validate_all_target_data(
        self,
        target_data_root: Path,
        dataset_types: Optional[List[str]] = None,
    ) -> Dict[str, QualityReport]:
        """
        Validate all consolidated target data files
        
        Args:
            target_data_root: Root directory containing target data model files
            dataset_types: Optional list of dataset types to validate (if None, validates all)
            
        Returns:
            Dictionary mapping dataset_type to QualityReport
        """
        tenant_dir = target_data_root / str(self.tenant_id)
        
        if not tenant_dir.exists():
            logger.warning(f"Tenant directory does not exist: {tenant_dir}")
            return {}
        
        reports = {}
        
        # If dataset_types specified, validate only those
        if dataset_types:
            for dataset_type in dataset_types:
                dataset_dir = tenant_dir / dataset_type
                if not dataset_dir.exists():
                    logger.warning(f"Dataset directory does not exist: {dataset_dir}")
                    continue
                
                # Find consolidated file (should be {dataset_type.lower()}.parquet or .csv)
                # Try parquet first, then CSV
                target_file = dataset_dir / f"{dataset_type.lower()}.parquet"
                if not target_file.exists():
                    target_file = dataset_dir / f"{dataset_type.lower()}.csv"
                # Also check for any parquet or csv files in the directory
                if not target_file.exists():
                    parquet_files = list(dataset_dir.glob("*.parquet"))
                    csv_files = list(dataset_dir.glob("*.csv"))
                    if parquet_files:
                        target_file = parquet_files[0]  # Use first parquet file found
                    elif csv_files:
                        target_file = csv_files[0]  # Use first CSV file found
                
                if target_file.exists():
                    report = self.validate_target_file(target_file, dataset_type)
                    reports[dataset_type] = report
        else:
            # Validate all dataset types found
            for dataset_dir in tenant_dir.iterdir():
                if not dataset_dir.is_dir():
                    continue
                
                dataset_type = dataset_dir.name
                
                # Find consolidated file
                target_file = dataset_dir / f"{dataset_type.lower()}.parquet"
                if not target_file.exists():
                    target_file = dataset_dir / f"{dataset_type.lower()}.csv"
                # Also check for any parquet or csv files in the directory
                if not target_file.exists():
                    parquet_files = list(dataset_dir.glob("*.parquet"))
                    csv_files = list(dataset_dir.glob("*.csv"))
                    if parquet_files:
                        target_file = parquet_files[0]  # Use first parquet file found
                    elif csv_files:
                        target_file = csv_files[0]  # Use first CSV file found
                
                if target_file.exists():
                    report = self.validate_target_file(target_file, dataset_type)
                    reports[dataset_type] = report
        
        return reports

