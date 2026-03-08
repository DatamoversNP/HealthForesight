"""
Canonical Base Models - Core principles for all datasets
Every canonical record includes these fields for lineage, versioning, and idempotency
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
import hashlib
import json


class CanonicalBase(BaseModel):
    """Base model for all canonical datasets - includes lineage and metadata"""
    
    # Multi-tenancy
    tenant_id: UUID = Field(..., description="Tenant identifier for multi-tenancy")
    
    # Source tracking
    source_system: str = Field(..., description="Source system identifier (e.g., 'EPIC', 'CERNER', 'PAYER_SYSTEM')")
    source_file_id: str = Field(..., description="Source file identifier")
    ingestion_id: UUID = Field(..., description="Ingestion run identifier")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Record last update timestamp")
    
    # Idempotency
    record_hash: Optional[str] = Field(None, description="Hash of record content for idempotency checks")
    
    def compute_hash(self) -> str:
        """Compute hash of record content (excluding metadata fields)"""
        # Get dict representation, exclude metadata fields
        data = self.model_dump(exclude={
            'tenant_id', 'source_system', 'source_file_id', 'ingestion_id',
            'created_at', 'updated_at', 'record_hash'
        })
        # Sort keys for consistent hashing
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def model_post_init(self, __context) -> None:
        """Compute hash after initialization if not provided"""
        if self.record_hash is None:
            self.record_hash = self.compute_hash()


class CoverageStatus(str, Enum):
    """Data coverage status"""
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"


class DatasetCoverage(BaseModel):
    """Metadata about dataset coverage and availability"""
    
    dataset_id: str = Field(..., description="Dataset identifier")
    dataset_version: str = Field(..., description="Dataset version")
    schema_version: str = Field(..., description="Schema version")
    
    # Coverage metrics
    coverage_status: CoverageStatus = Field(..., description="Overall coverage status")
    available_fields: list[str] = Field(default_factory=list, description="Fields that are available")
    partial_fields: list[str] = Field(default_factory=list, description="Fields that are partially available")
    missing_fields: list[str] = Field(default_factory=list, description="Fields that are missing")
    
    # Confidence and quality
    confidence_penalty: float = Field(0.0, ge=0.0, le=1.0, description="Confidence penalty due to missingness (0-1)")
    completeness_score: float = Field(1.0, ge=0.0, le=1.0, description="Overall completeness score (0-1)")
    
    # Source metadata
    source_system: str = Field(..., description="Source system")
    ingestion_id: UUID = Field(..., description="Ingestion run ID")
    load_start_time: datetime = Field(..., description="Load start time")
    load_end_time: Optional[datetime] = Field(None, description="Load end time")
    
    # Validation
    validation_report_uri: Optional[str] = Field(None, description="URI to validation report")
    record_count: int = Field(0, description="Total record count")
    valid_record_count: int = Field(0, description="Valid record count")
    error_count: int = Field(0, description="Error count")

