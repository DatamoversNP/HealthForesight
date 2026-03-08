"""
Pipeline Metadata Models
Defines the structure for metadata-driven ingestion pipelines
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class PipelineMode(str, Enum):
    """Pipeline ingestion mode"""
    APPEND = "APPEND"  # Append new records
    REPLACE = "REPLACE"  # Replace existing data
    UPSERT = "UPSERT"  # Update existing or insert new


class DeduplicationStrategy(str, Enum):
    """Deduplication strategy"""
    NONE = "NONE"  # No deduplication
    HASH = "HASH"  # Use record hash
    KEY_FIELDS = "KEY_FIELDS"  # Use specified key fields
    SOURCE_ID = "SOURCE_ID"  # Use source record ID


class FieldMapping(BaseModel):
    """Field mapping from source to target"""
    source_field: str = Field(..., description="Source field name")
    target_field: str = Field(..., description="Target canonical field name")
    transform_function: Optional[str] = Field(None, description="Transform function (e.g., 'to_date', 'to_float', 'normalize_string')")
    default_value: Optional[Any] = Field(None, description="Default value if source field is missing")
    required: bool = Field(False, description="Whether this field is required in target")


class DeduplicationConfig(BaseModel):
    """Deduplication configuration"""
    strategy: DeduplicationStrategy = Field(DeduplicationStrategy.HASH, description="Deduplication strategy")
    key_fields: Optional[List[str]] = Field(None, description="Key fields for KEY_FIELDS strategy")
    source_id_field: Optional[str] = Field(None, description="Source ID field for SOURCE_ID strategy")


class PipelineMetadata(BaseModel):
    """Complete pipeline metadata definition"""
    
    # Pipeline Identity
    pipeline_id: UUID = Field(..., description="Unique pipeline identifier")
    pipeline_name: str = Field(..., description="Pipeline name")
    pipeline_description: Optional[str] = Field(None, description="Pipeline description")
    version: str = Field("1.0", description="Pipeline version")
    
    # Source Configuration
    source_type: str = Field(..., description="Source type (e.g., 'CSV', 'PARQUET', 'JSON', 'API')")
    source_format: Optional[str] = Field(None, description="Source format details")
    source_schema: Optional[Dict[str, Any]] = Field(None, description="Source schema definition")
    
    # Target Configuration
    target_dataset_type: str = Field(..., description="Target canonical dataset type (e.g., 'CLAIMS_LINES', 'MEMBER_MASTER')")
    target_model: str = Field(..., description="Target canonical model name (e.g., 'ClaimLine', 'MemberMaster')")
    
    # Field Mappings
    field_mappings: List[FieldMapping] = Field(..., description="Field mappings from source to target")
    
    # Ingestion Configuration
    mode: PipelineMode = Field(PipelineMode.APPEND, description="Ingestion mode")
    deduplication: DeduplicationConfig = Field(default_factory=lambda: DeduplicationConfig(), description="Deduplication configuration")
    
    # Control Fields (added to target)
    control_fields: Dict[str, Any] = Field(
        default_factory=lambda: {
            "created_at": "CURRENT_TIMESTAMP",
            "updated_at": "CURRENT_TIMESTAMP",
            "active_flag": True,
            "effective_date": "CURRENT_TIMESTAMP",  # Default to current timestamp (record effective from creation)
            "expiration_date": None,  # Optional - records don't expire by default
        },
        description="Control fields to add to target records"
    )
    
    # Validation Rules
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Validation rules")
    required_fields: List[str] = Field(default_factory=list, description="Required fields in target")
    
    # Processing Configuration
    batch_size: int = Field(10000, ge=1, description="Batch size for processing")
    error_threshold: float = Field(0.05, ge=0.0, le=1.0, description="Error threshold (0-1)")
    continue_on_error: bool = Field(True, description="Continue processing on errors")
    
    # Status
    active: bool = Field(True, description="Whether pipeline is active")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="User who created the pipeline")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    notes: Optional[str] = Field(None, description="Additional notes")


class PipelineRun(BaseModel):
    """Pipeline run execution record"""
    run_id: UUID = Field(..., description="Unique run identifier")
    pipeline_id: UUID = Field(..., description="Pipeline identifier")
    status: str = Field(..., description="Run status (PENDING/PROCESSING/COMPLETED/FAILED)")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    records_processed: int = Field(0, description="Records processed")
    records_succeeded: int = Field(0, description="Records succeeded")
    records_failed: int = Field(0, description="Records failed")
    records_duplicated: int = Field(0, description="Records deduplicated")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Error details")
    source_uri: Optional[str] = Field(None, description="Source data URI")
    output_uri: Optional[str] = Field(None, description="Output data URI")

