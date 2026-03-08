"""
Comprehensive Ingestion Processor
Handles comprehensive canonical schemas with partial availability support
"""
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from uuid import UUID
from datetime import datetime
import pandas as pd
import polars as pl

from uepi_common.ingestion.format_detector import FormatDetector
from uepi_common.ingestion.validator import DataValidator
from uepi_common.data_contracts.canonical_base import CoverageStatus, DatasetCoverage


class ComprehensiveIngestionProcessor:
    """Process ingestion with comprehensive canonical schemas and partial availability"""
    
    def __init__(
        self,
        tenant_id: UUID,
        dataset_type: str,
        source_system: str = "UNKNOWN",
        ingestion_id: Optional[UUID] = None,
    ):
        """
        Initialize comprehensive ingestion processor
        
        Args:
            tenant_id: Tenant identifier
            dataset_type: Dataset type (e.g., "CLAIMS_LINES", "MEMBER_MASTER", "ELIGIBILITY_ENROLLMENT")
            source_system: Source system identifier
            ingestion_id: Ingestion run identifier
        """
        self.tenant_id = tenant_id
        self.dataset_type = dataset_type
        self.source_system = source_system
        self.ingestion_id = ingestion_id or UUID("00000000-0000-0000-0000-000000000000")
        
        self.format_detector = FormatDetector()
        self.schema_mapper = None  # Will be initialized based on dataset type
        self.validator = DataValidator(dataset_type)
    
    def analyze_schema(self, file_path: str | Path) -> Dict[str, Any]:
        """Analyze file schema and suggest mappings to comprehensive canonical schema"""
        detected_format = self.format_detector.detect_format(file_path)
        df_sample = self.format_detector.parse_file(file_path, format=detected_format)
        
        source_columns = df_sample.columns.tolist()
        sample_values = {col: df_sample[col].head(5).tolist() for col in source_columns}
        
        # Get canonical schema for this dataset type
        canonical_schema = self._get_canonical_schema()
        canonical_fields = canonical_schema.get("fields", {})
        
        # Suggest mappings
        suggested_mapping = self._suggest_mappings(source_columns, canonical_fields)
        
        # Calculate coverage
        mapped_count = len(suggested_mapping)
        total_canonical = len([f for f in canonical_fields.values() if f.get("required", False)])
        unmapped_source = [col for col in source_columns if col not in suggested_mapping.values()]
        unmapped_canonical = [
            field_name for field_name, field_def in canonical_fields.items()
            if field_def.get("required", False) and field_name not in suggested_mapping
        ]
        
        return {
            "format": detected_format,
            "source_columns": [{"name": col, "sample_values": sample_values.get(col, [])} for col in source_columns],
            "canonical_schema": [
                {
                    "name": field_name,
                    "type": field_def.get("type"),
                    "required": field_def.get("required", False),
                    "description": field_def.get("description"),
                }
                for field_name, field_def in canonical_fields.items()
            ],
            "suggested_mapping": suggested_mapping,
            "coverage": {
                "mapped": mapped_count,
                "total_canonical": total_canonical,
                "unmapped_source": unmapped_source,
                "unmapped_canonical": unmapped_canonical,
                "completeness_score": mapped_count / total_canonical if total_canonical > 0 else 0.0,
            }
        }
    
    def _get_canonical_schema(self) -> Dict[str, Any]:
        """Get canonical schema for dataset type"""
        # Map dataset types to comprehensive canonical models
        schemas = {
            "CLAIMS_LINES": {
                "fields": {
                    "claim_line_id": {"type": "string", "required": True, "description": "Claim line identifier"},
                    "claim_id": {"type": "string", "required": True, "description": "Claim identifier"},
                    "member_id": {"type": "string", "required": True, "description": "Member identifier"},
                    "cpt_hcpcs": {"type": "string", "required": False, "description": "CPT/HCPCS code"},
                    "service_date_from": {"type": "date", "required": True, "description": "Service date from"},
                    "service_date_to": {"type": "date", "required": False, "description": "Service date to"},
                    "place_of_service": {"type": "string", "required": True, "description": "Place of service code"},
                    "service_category": {"type": "string", "required": True, "description": "Service category"},
                    "allowed_amount": {"type": "float", "required": True, "description": "Allowed amount"},
                    "paid_amount": {"type": "float", "required": True, "description": "Paid amount"},
                    "in_network_flag": {"type": "bool", "required": True, "description": "In-network flag"},
                    "rendering_provider_id": {"type": "string", "required": False, "description": "Rendering provider"},
                    "facility_id": {"type": "string", "required": False, "description": "Facility identifier"},
                },
                "aliases": {
                    "claim_line_id": ["clm_line_id", "line_id", "claim_line"],
                    "claim_id": ["clm_id", "claim_number"],
                    "member_id": ["member", "mem_id", "patient_id"],
                    "cpt_hcpcs": ["cpt", "hcpcs", "procedure_code"],
                    "service_date_from": ["service_date", "date_of_service", "dos"],
                    "place_of_service": ["pos", "pos_code"],
                    "allowed_amount": ["allowed", "allowed_amt"],
                    "paid_amount": ["paid", "paid_amt"],
                    "in_network_flag": ["in_network", "network_flag"],
                }
            },
            "MEMBER_MASTER": {
                "fields": {
                    "member_id": {"type": "string", "required": True, "description": "Member identifier"},
                    "dob": {"type": "date", "required": False, "description": "Date of birth"},
                    "age": {"type": "int", "required": False, "description": "Age"},
                    "gender": {"type": "string", "required": False, "description": "Gender"},
                    "address_zip5": {"type": "string", "required": False, "description": "ZIP code"},
                    "state": {"type": "string", "required": False, "description": "State"},
                },
                "aliases": {
                    "member_id": ["member", "mem_id", "patient_id"],
                    "dob": ["date_of_birth", "birth_date"],
                }
            },
            "ELIGIBILITY_ENROLLMENT": {
                "fields": {
                    "member_id": {"type": "string", "required": True, "description": "Member identifier"},
                    "coverage_month": {"type": "string", "required": True, "description": "Coverage month (YYYY-MM)"},
                    "plan_id": {"type": "string", "required": True, "description": "Plan identifier"},
                    "line_of_business": {"type": "string", "required": True, "description": "Line of business"},
                    "coverage_status": {"type": "string", "required": True, "description": "Coverage status"},
                },
                "aliases": {
                    "member_id": ["member", "mem_id"],
                    "coverage_month": ["month", "enrollment_month"],
                    "line_of_business": ["lob"],
                }
            },
            "PROVIDER_MASTER": {
                "fields": {
                    "provider_id": {"type": "string", "required": True, "description": "Provider identifier"},
                    "npi": {"type": "string", "required": False, "description": "NPI"},
                    "provider_name": {"type": "string", "required": False, "description": "Provider name"},
                    "specialty_primary": {"type": "string", "required": False, "description": "Primary specialty"},
                    "provider_type": {"type": "string", "required": True, "description": "Provider type"},
                },
                "aliases": {
                    "provider_id": ["prov_id", "provider"],
                    "npi": ["npi_number"],
                }
            },
        }
        
        return schemas.get(self.dataset_type, {"fields": {}, "aliases": {}})
    
    def _suggest_mappings(self, source_columns: List[str], canonical_fields: Dict[str, Any]) -> Dict[str, str]:
        """Suggest mappings from source columns to canonical fields"""
        suggestions = {}
        source_normalized = {col.lower().replace('_', '').replace('-', '').replace(' ', ''): col for col in source_columns}
        
        canonical_schema = self._get_canonical_schema()
        aliases = canonical_schema.get("aliases", {})
        
        for canonical_field, field_def in canonical_fields.items():
            # 1. Exact match
            if canonical_field.lower() in source_normalized:
                suggestions[canonical_field] = source_normalized[canonical_field.lower()]
                continue
            
            # 2. Alias match
            for alias in aliases.get(canonical_field, []):
                alias_normalized = alias.lower().replace('_', '').replace('-', '').replace(' ', '')
                if alias_normalized in source_normalized:
                    suggestions[canonical_field] = source_normalized[alias_normalized]
                    break
        
        return suggestions
    
    def process_file(
        self,
        file_path: str | Path,
        mapping_config: Optional[Dict[str, Any]] = None,
        auto_detect_schema: bool = True,
    ) -> Dict[str, Any]:
        """
        Process file with comprehensive canonical schema
        
        Returns:
            {
                "success": bool,
                "record_count": int,
                "records_valid": int,
                "records_invalid": int,
                "coverage": DatasetCoverage,
                "raw_zone_uri": str,
                "curated_zone_uri": str,
                "errors": List[Dict],
                "warnings": List[Dict],
            }
        """
        # Detect format and parse
        detected_format = self.format_detector.detect_format(file_path)
        df_raw = self.format_detector.parse_file(file_path, format=detected_format)
        
        record_count = len(df_raw)
        
        # Apply mapping if provided
        if mapping_config:
            # Apply manual mapping
            df_mapped = self._apply_mapping(df_raw, mapping_config)
        elif auto_detect_schema:
            # Auto-detect and apply
            canonical_schema = self._get_canonical_schema()
            suggested = self._suggest_mappings(df_raw.columns.tolist(), canonical_schema["fields"])
            df_mapped = self._apply_mapping(df_raw, {"mappings": suggested})
        else:
            df_mapped = df_raw
        
        # Add canonical base fields
        df_mapped = df_mapped.with_columns([
            pl.lit(str(self.tenant_id)).alias("tenant_id"),
            pl.lit(self.source_system).alias("source_system"),
            pl.lit(Path(file_path).name).alias("source_file_id"),
            pl.lit(str(self.ingestion_id)).alias("ingestion_id"),
            pl.lit(datetime.utcnow().isoformat()).alias("created_at"),
            pl.lit(datetime.utcnow().isoformat()).alias("updated_at"),
        ])
        
        # Calculate coverage
        canonical_schema = self._get_canonical_schema()
        canonical_fields = canonical_schema.get("fields", {})
        available_fields = [col for col in df_mapped.columns if col in canonical_fields]
        missing_required = [
            field_name for field_name, field_def in canonical_fields.items()
            if field_def.get("required", False) and field_name not in df_mapped.columns
        ]
        
        completeness_score = len(available_fields) / len(canonical_fields) if canonical_fields else 1.0
        confidence_penalty = len(missing_required) * 0.1  # 10% penalty per missing required field
        
        coverage_status = CoverageStatus.AVAILABLE if not missing_required else CoverageStatus.PARTIAL
        coverage = DatasetCoverage(
            dataset_id=str(self.ingestion_id),
            dataset_version="1.0",
            schema_version="1.0",
            coverage_status=coverage_status,
            available_fields=available_fields,
            missing_fields=missing_required,
            confidence_penalty=min(confidence_penalty, 1.0),
            completeness_score=completeness_score,
            source_system=self.source_system,
            ingestion_id=self.ingestion_id,
            load_start_time=datetime.utcnow(),
            record_count=record_count,
            valid_record_count=record_count,  # Simplified - would validate in real implementation
        )
        
        # Save to raw and target data model zones (simplified for file storage)
        raw_zone_uri = f"local_raw://{self.tenant_id}/{self.dataset_type}/{Path(file_path).name}"
        curated_zone_uri = f"local_target://{self.tenant_id}/{self.dataset_type}/{datetime.utcnow().strftime('%Y/%m')}/data.parquet"
        
        # Write to local storage (simplified)
        output_path = Path(f"data/target_data_model/{self.tenant_id}/{self.dataset_type}")
        output_path.mkdir(parents=True, exist_ok=True)
        df_mapped.write_parquet(output_path / f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.parquet")
        
        return {
            "success": len(missing_required) == 0,
            "record_count": record_count,
            "records_valid": record_count,
            "records_invalid": 0,
            "coverage": coverage.model_dump(),
            "raw_zone_uri": raw_zone_uri,
            "curated_zone_uri": curated_zone_uri,
            "errors": [],
            "warnings": [{"field": f, "message": f"Missing required field: {f}"} for f in missing_required] if missing_required else [],
        }
    
    def _apply_mapping(self, df: pd.DataFrame, mapping_config: Dict[str, Any]) -> pl.DataFrame:
        """Apply column mapping to DataFrame"""
        mappings = mapping_config.get("mappings", {})
        df_mapped = df.copy()
        
        # Rename columns
        rename_dict = {v: k for k, v in mappings.items() if v in df_mapped.columns}
        df_mapped = df_mapped.rename(columns=rename_dict)
        
        return pl.DataFrame(df_mapped)

