"""Ingestion Manifest data contract - metadata for data ingestion"""
from datetime import datetime
from enum import Enum
from typing import Optional, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class DatasetType(str, Enum):
    """Dataset type enumeration"""
    CLAIMS_LINES = "CLAIMS_LINES"
    ENROLLMENT = "ENROLLMENT"
    PROVIDERS = "PROVIDERS"
    BENEFIT_DESIGN = "BENEFIT_DESIGN"
    POLICY_EXPORT = "POLICY_EXPORT"
    PRIOR_AUTH_LOGS = "PRIOR_AUTH_LOGS"  # Phase 2
    APPEALS = "APPEALS"  # Phase 2


class IngestionMode(str, Enum):
    """Ingestion mode enumeration"""
    MANUAL_UPLOAD = "MANUAL_UPLOAD"
    SCHEDULED = "SCHEDULED"
    BACKFILL = "BACKFILL"
    API = "API"  # Future: API-based ingestion


class IngestionManifest(BaseModel):
    """Ingestion Manifest - metadata for data ingestion
    
    Every ingestion must include a manifest file that describes:
    - What dataset is being ingested
    - Source files and their schemas
    - Validation rules
    - Expected record counts
    
    Schema Version: 1.0
    Format: JSON
    """
    
    # Manifest Header
    manifest_id: UUID = Field(default_factory=uuid4, description="Unique manifest identifier")
    tenant_id: UUID = Field(..., description="Tenant ID for multi-tenancy")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Manifest creation timestamp")
    created_by: Optional[str] = Field(None, description="User/process that created the manifest")
    
    # Dataset Information
    dataset_type: DatasetType = Field(..., description="Type of dataset being ingested")
    ingestion_mode: IngestionMode = Field(..., description="Ingestion mode")
    
    # Source Files
    source_files: list[dict[str, str]] = Field(
        ..., 
        description="List of source files with keys: 'uri' (blob path or URL), 'format' (CSV/Parquet/JSON), 'record_count' (expected)"
    )
    
    # Temporal Coverage
    data_start_date: Optional[str] = Field(None, description="Earliest date in dataset (YYYY-MM-DD)")
    data_end_date: Optional[str] = Field(None, description="Latest date in dataset (YYYY-MM-DD)")
    
    # Scope
    lobs: list[str] = Field(default_factory=list, description="Lines of business covered in dataset")
    markets: list[str] = Field(default_factory=list, description="Markets/regions covered in dataset")
    
    # Validation Rules
    schema_version: str = Field(default="1.0", description="Expected schema version")
    required_fields: list[str] = Field(default_factory=list, description="Required field names for validation")
    validation_rules: Optional[dict[str, Any]] = Field(None, description="Custom validation rules (JSON)")
    
    # Expected Metrics
    expected_record_count: Optional[int] = Field(None, ge=0, description="Expected total record count")
    expected_file_size_mb: Optional[float] = Field(None, ge=0, description="Expected total file size in MB")
    
    # Processing Instructions
    incremental: bool = Field(default=False, description="Whether this is an incremental ingestion (new months only)")
    replace_existing: bool = Field(default=False, description="Whether to replace existing data for overlapping periods")
    partition_by: Optional[list[str]] = Field(None, description="Partitioning strategy (e.g., ['year', 'month', 'lob', 'market'])")
    
    # Additional Context
    source_system: Optional[str] = Field(None, description="Source system (e.g., 'Claims Adjudication', 'Enrollment System')")
    notes: Optional[str] = Field(None, description="Additional notes for ingestion")
    
    class Config:
        json_schema_extra = {
            "example": {
                "manifest_id": "550e8400-e29b-41d4-a716-446655440000",
                "tenant_id": "00000000-0000-0000-0000-000000000002",
                "created_at": "2024-01-15T10:00:00Z",
                "created_by": "data_engineer@payer.com",
                "dataset_type": "CLAIMS_LINES",
                "ingestion_mode": "SCHEDULED",
                "source_files": [
                    {
                        "uri": "s3://uepi-data/raw/claims/2024-01/claims_202401.csv",
                        "format": "CSV",
                        "record_count": 5000000
                    }
                ],
                "data_start_date": "2024-01-01",
                "data_end_date": "2024-01-31",
                "lobs": ["Commercial", "Medicare"],
                "markets": ["CA", "TX"],
                "schema_version": "1.0",
                "required_fields": ["claim_id", "claim_line_id", "member_id", "provider_id", "service_date"],
                "expected_record_count": 5000000,
                "expected_file_size_mb": 2500.0,
                "incremental": True,
                "partition_by": ["year", "month", "lob", "market"],
                "source_system": "Claims Adjudication System",
            }
        }

