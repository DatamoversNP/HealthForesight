"""Schema validation for ingestion pipeline"""
from typing import Any, Optional
from uuid import UUID
import polars as pl

from uepi_common.data_contracts.claims import ClaimsLine
from uepi_common.data_contracts.enrollment import EnrollmentRecord
from uepi_common.data_contracts.providers import ProviderRecord
from uepi_common.data_contracts.benefits import BenefitDesignRecord
from uepi_common.data_contracts.manifest import DatasetType


class ValidationError(Exception):
    """Validation error with details"""
    def __init__(self, field: str, message: str, row: Optional[int] = None, value: Optional[Any] = None):
        self.field = field
        self.message = message
        self.row = row
        self.value = value
        super().__init__(f"{field}: {message} (row={row}, value={value})")


class ValidationResult:
    """Result of validation operation"""
    def __init__(
        self,
        valid: bool,
        record_count: int,
        valid_count: int,
        error_count: int,
        errors: list[dict[str, Any]],
        warnings: list[dict[str, Any]] = None,
    ):
        self.valid = valid
        self.record_count = record_count
        self.valid_count = valid_count
        self.error_count = error_count
        self.errors = errors or []
        self.warnings = warnings or []
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "valid": self.valid,
            "record_count": self.record_count,
            "valid_count": self.valid_count,
            "error_count": self.error_count,
            "errors": self.errors,
            "warnings": self.warnings or [],
        }


class DataValidator:
    """Validates ingested data against canonical data contracts"""
    
    def __init__(self, dataset_type: DatasetType):
        """Initialize validator for dataset type
        
        Args:
            dataset_type: Type of dataset being validated
        """
        self.dataset_type = dataset_type
        self.model_class = self._get_model_class()
    
    def _get_model_class(self):
        """Get Pydantic model class for dataset type"""
        model_map = {
            DatasetType.CLAIMS_LINES: ClaimsLine,
            DatasetType.ENROLLMENT: EnrollmentRecord,
            DatasetType.PROVIDERS: ProviderRecord,
            DatasetType.BENEFIT_DESIGN: BenefitDesignRecord,
        }
        return model_map.get(self.dataset_type)
    
    def validate_dataframe(
        self,
        df: pl.DataFrame,
        strict: bool = False,
    ) -> ValidationResult:
        """Validate DataFrame against data contract
        
        Args:
            df: Polars DataFrame to validate
            strict: If True, stop on first error; if False, collect all errors
            
        Returns:
            ValidationResult with validation status and errors
        """
        if self.model_class is None:
            return ValidationResult(
                valid=False,
                record_count=len(df),
                valid_count=0,
                error_count=len(df),
                errors=[{"field": "dataset_type", "message": f"Unknown dataset type: {self.dataset_type}"}],
            )
        
        errors = []
        warnings = []
        valid_records = []
        
        # Validate each row
        for idx, row in enumerate(df.iter_rows(named=True)):
            try:
                # Convert row to dict and validate with Pydantic
                record = self.model_class(**row)
                valid_records.append(record)
            except Exception as e:
                # Extract field-level errors from Pydantic
                error_dict = {
                    "row": idx + 1,  # 1-indexed for user-friendliness
                    "message": str(e),
                    "row_data": row,
                }
                
                # Try to extract field-specific errors
                if hasattr(e, "errors") and isinstance(e.errors(), list):
                    error_dict["field_errors"] = []
                    for field_error in e.errors():
                        error_dict["field_errors"].append({
                            "field": field_error.get("loc", ["unknown"])[-1],
                            "message": field_error.get("msg", "Validation error"),
                            "value": field_error.get("input"),
                        })
                
                errors.append(error_dict)
                
                if strict:
                    break
        
        # Check for data quality warnings
        warnings.extend(self._check_data_quality(df, valid_records))
        
        valid_count = len(valid_records)
        error_count = len(errors)
        record_count = len(df)
        
        return ValidationResult(
            valid=error_count == 0,
            record_count=record_count,
            valid_count=valid_count,
            error_count=error_count,
            errors=errors,
            warnings=warnings,
        )
    
    def validate_file(
        self,
        file_path: str,
        format: str = "parquet",
        strict: bool = False,
    ) -> ValidationResult:
        """Validate a file against data contract
        
        Args:
            file_path: Path to file (local or blob URI)
            format: File format ('parquet', 'csv', 'json')
            strict: If True, stop on first error
            
        Returns:
            ValidationResult with validation status and errors
        """
        # Read file based on format
        if format.lower() == "parquet":
            df = pl.read_parquet(file_path)
        elif format.lower() == "csv":
            df = pl.read_csv(file_path)
        elif format.lower() == "json":
            df = pl.read_json(file_path)
        else:
            return ValidationResult(
                valid=False,
                record_count=0,
                valid_count=0,
                error_count=0,
                errors=[{"field": "format", "message": f"Unsupported format: {format}"}],
            )
        
        return self.validate_dataframe(df, strict=strict)
    
    def _check_data_quality(
        self,
        df: pl.DataFrame,
        valid_records: list,
    ) -> list[dict[str, Any]]:
        """Check for data quality issues (warnings, not errors)
        
        Args:
            df: Original DataFrame
            valid_records: List of validated records
            
        Returns:
            List of warning dictionaries
        """
        warnings = []
        
        # Check for missing values in critical fields
        if self.dataset_type == DatasetType.CLAIMS_LINES:
            critical_fields = ["claim_id", "member_id", "provider_id", "service_date"]
            for field in critical_fields:
                if field in df.columns:
                    null_count = df[field].null_count()
                    if null_count > 0:
                        warnings.append({
                            "type": "missing_values",
                            "field": field,
                            "count": null_count,
                            "message": f"{null_count} rows have missing {field}",
                        })
            
            # Check for negative amounts
            amount_fields = ["allowed_amount", "paid_amount"]
            for field in amount_fields:
                if field in df.columns:
                    negative_count = df.filter(pl.col(field) < 0).height
                    if negative_count > 0:
                        warnings.append({
                            "type": "negative_amounts",
                            "field": field,
                            "count": negative_count,
                            "message": f"{negative_count} rows have negative {field}",
                        })
            
            # Check for future dates
            if "service_date" in df.columns:
                from datetime import date
                today = date.today()
                future_count = df.filter(pl.col("service_date") > today).height
                if future_count > 0:
                    warnings.append({
                        "type": "future_dates",
                        "field": "service_date",
                        "count": future_count,
                        "message": f"{future_count} rows have service_date in the future",
                    })
        
        # Check for duplicate primary keys
        if self.dataset_type == DatasetType.CLAIMS_LINES:
            if "claim_line_id" in df.columns:
                duplicates = df.filter(pl.col("claim_line_id").is_duplicated())
                if duplicates.height > 0:
                    warnings.append({
                        "type": "duplicate_keys",
                        "field": "claim_line_id",
                        "count": duplicates.height,
                        "message": f"{duplicates.height} rows have duplicate claim_line_id",
                    })
        
        return warnings

