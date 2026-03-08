"""Flexible ingestion processor that handles format variations"""
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import pandas as pd
import polars as pl

from uepi_common.ingestion.format_detector import FormatDetector
from uepi_common.ingestion.schema_mapper import SchemaMapper
from uepi_common.ingestion.validator import DataValidator
from uepi_common.data_contracts.manifest import DatasetType


class FlexibleIngestionProcessor:
    """Process ingestion with flexible format and schema handling"""
    
    def __init__(
        self,
        dataset_type: DatasetType,
        mapping_config: Optional[Dict[str, Any]] = None,
        auto_detect: bool = True,
        canonical_schema: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize flexible ingestion processor
        
        Args:
            dataset_type: Type of dataset being ingested
            mapping_config: Optional manual mapping configuration
            auto_detect: Whether to auto-detect column mappings
            canonical_schema: Canonical schema for auto-detection
        """
        self.dataset_type = dataset_type
        self.mapping_config = mapping_config
        self.auto_detect = auto_detect
        self.canonical_schema = canonical_schema or self._get_default_schema(dataset_type)
        self.format_detector = FormatDetector()
        self.schema_mapper = None
        self.validator = DataValidator(dataset_type)
    
    def _get_default_schema(self, dataset_type: DatasetType) -> Dict[str, Any]:
        """Get default canonical schema for dataset type"""
        if dataset_type == DatasetType.CLAIMS_LINES:
            return {
                "fields": {
                    "claim_id": {"type": "string", "required": True},
                    "claim_line_id": {"type": "string", "required": True},
                    "member_id": {"type": "string", "required": True},
                    "service_from_date": {"type": "date", "required": True},
                    "service_to_date": {"type": "date", "required": False},
                    "paid_date": {"type": "date", "required": False},
                    "lob": {"type": "string", "required": True},
                    "market": {"type": "string", "required": True},
                    "cpt_hcpcs": {"type": "string", "required": True},
                    "rendering_npi": {"type": "string", "required": True},
                    "allowed_amount": {"type": "float", "required": True},
                    "paid_amount": {"type": "float", "required": True},
                    "units": {"type": "float", "required": True},
                    "in_network_flag": {"type": "bool", "required": True},
                    "place_of_service": {"type": "string", "required": False},
                },
                "aliases": {
                    "claim_id": ["clm_id", "claim_number", "claim_num", "claim_no"],
                    "claim_line_id": ["line_id", "line_number", "line_num"],
                    "member_id": ["member", "mem_id", "patient_id", "patient", "subscriber_id"],
                    "service_from_date": ["service_date", "date_of_service", "dos", "from_date"],
                    "service_to_date": ["to_date", "end_date"],
                    "paid_date": ["payment_date", "paid_dt"],
                    "cpt_hcpcs": ["cpt", "hcpcs", "procedure_code", "proc_code"],
                    "rendering_npi": ["npi", "provider_npi", "rendering_provider"],
                    "allowed_amount": ["allowed", "allowed_amt", "charge_amount"],
                    "paid_amount": ["paid", "paid_amt", "payment_amount"],
                    "in_network_flag": ["in_network", "network_flag", "network"],
                }
            }
        elif dataset_type == DatasetType.ENROLLMENT:
            return {
                "fields": {
                    "member_id": {"type": "string", "required": True},
                    "lob": {"type": "string", "required": True},
                    "market": {"type": "string", "required": True},
                    "enrolled_flag": {"type": "bool", "required": True},
                    "gender": {"type": "string", "required": False},
                    "dob_year": {"type": "int", "required": False},
                    "risk_score": {"type": "float", "required": False},
                },
                "aliases": {
                    "member_id": ["member", "mem_id", "patient_id", "subscriber_id"],
                    "enrolled_flag": ["enrolled", "active", "is_enrolled"],
                }
            }
        elif dataset_type == DatasetType.PROVIDERS:
            return {
                "fields": {
                    "npi": {"type": "string", "required": True},
                    "provider_name": {"type": "string", "required": True},
                    "specialty": {"type": "string", "required": True},
                    "market": {"type": "string", "required": True},
                    "facility_flag": {"type": "bool", "required": True},
                },
                "aliases": {
                    "npi": ["provider_npi", "npi_number"],
                    "provider_name": ["name", "provider", "facility_name"],
                }
            }
        else:
            return {"fields": {}, "aliases": {}}
    
    def process_file(
        self,
        file_path: str | Path,
        format: Optional[str] = None,
        mapping_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a file with flexible format and schema handling
        
        Returns:
            {
                "success": bool,
                "records_processed": int,
                "records_valid": int,
                "records_invalid": int,
                "errors": List[Dict],
                "warnings": List[str],
                "mapping_applied": Dict[str, str],
                "dataframe": pd.DataFrame,
            }
        """
        errors = []
        warnings = []
        
        try:
            # Detect and parse file format
            detected_format = format or self.format_detector.detect_format(file_path)
            df = self.format_detector.parse_file(file_path, detected_format)
            
            if df.empty:
                return {
                    "success": False,
                    "records_processed": 0,
                    "records_valid": 0,
                    "records_invalid": 0,
                    "errors": [{"type": "EMPTY_FILE", "message": "File contains no data"}],
                    "warnings": [],
                    "mapping_applied": {},
                    "dataframe": pd.DataFrame(),
                }
            
            # Auto-detect mapping if enabled and no manual config provided
            if self.auto_detect and not (mapping_config or self.mapping_config):
                auto_mapping = SchemaMapper.auto_detect_mapping(df, self.canonical_schema)
                self.mapping_config = auto_mapping
                warnings.append(f"Auto-detected {len(auto_mapping['column_mappings'])} column mappings")
            
            # Use provided mapping config or instance config
            final_mapping = mapping_config or self.mapping_config or {}
            
            # Create schema mapper
            self.schema_mapper = SchemaMapper(final_mapping)
            
            # Transform data
            df_transformed = self.schema_mapper.transform(df)
            
            # Check required fields
            missing_fields = self.schema_mapper.validate_required_fields(df_transformed)
            if missing_fields:
                errors.append({
                    "type": "MISSING_REQUIRED_FIELDS",
                    "message": f"Missing required fields: {', '.join(missing_fields)}",
                    "fields": missing_fields,
                })
            
            # Convert to polars DataFrame for validation
            try:
                import polars as pl
                df_pl = pl.from_pandas(df_transformed)
            except ImportError:
                # Fallback: create minimal validation result
                validation_result = {
                    "valid": True,
                    "errors": [],
                    "warnings": [],
                    "invalid_rows": [],
                }
            else:
                # Validate data
                validation_result = self.validator.validate_dataframe(
                    df_pl,
                    strict=False,
                )
                if hasattr(validation_result, 'to_dict'):
                    validation_result = validation_result.to_dict()
            
            # Combine errors
            all_errors = errors + validation_result.get("errors", [])
            all_warnings = warnings + validation_result.get("warnings", [])
            
            # Count valid/invalid records
            records_processed = len(df_transformed)
            records_valid = records_processed - len(validation_result.get("invalid_rows", []))
            records_invalid = len(validation_result.get("invalid_rows", []))
            
            return {
                "success": len(missing_fields) == 0 and len(all_errors) == 0,
                "records_processed": records_processed,
                "records_valid": records_valid,
                "records_invalid": records_invalid,
                "errors": all_errors,
                "warnings": all_warnings,
                "mapping_applied": final_mapping.get("column_mappings", {}),
                "dataframe": df_transformed,
                "validation_result": validation_result,
            }
        
        except Exception as e:
            return {
                "success": False,
                "records_processed": 0,
                "records_valid": 0,
                "records_invalid": 0,
                "errors": [{"type": "PROCESSING_ERROR", "message": str(e)}],
                "warnings": [],
                "mapping_applied": {},
                "dataframe": pd.DataFrame(),
            }
    
    def get_schema_suggestion(self, file_path: str | Path) -> Dict[str, Any]:
        """Analyze file and suggest schema mapping"""
        try:
            df = self.format_detector.parse_file(file_path)
            auto_mapping = SchemaMapper.auto_detect_mapping(df, self.canonical_schema)
            
            return {
                "detected_format": self.format_detector.detect_format(file_path),
                "source_columns": list(df.columns),
                "sample_rows": df.head(3).to_dict('records'),
                "suggested_mapping": auto_mapping,
                "coverage": {
                    "mapped": len(auto_mapping["column_mappings"]),
                    "total_canonical": len(self.canonical_schema.get("fields", {})),
                    "unmapped_source": [col for col in df.columns if col not in auto_mapping["column_mappings"]],
                }
            }
        except Exception as e:
            return {
                "error": str(e),
                "detected_format": None,
                "source_columns": [],
                "sample_rows": [],
                "suggested_mapping": {},
                "coverage": {},
            }

