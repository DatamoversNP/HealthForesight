"""Database models for canonical data (ClaimsLine, EnrollmentRecord, ProviderRecord)"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, Date, Boolean, Numeric, Text, Index, ForeignKey,
    DateTime, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY, JSONB
from sqlalchemy.orm import relationship

from uepi_api.database import Base


class ClaimsLineDB(Base):
    """Database model for ClaimsLine canonical data"""
    __tablename__ = "claims_lines"
    __table_args__ = (
        # Composite primary key
        Index("ix_claims_lines_tenant_claim_line", "tenant_id", "claim_line_id"),
        Index("ix_claims_lines_tenant_member", "tenant_id", "member_id"),
        Index("ix_claims_lines_tenant_provider", "tenant_id", "provider_id"),
        Index("ix_claims_lines_service_date", "service_date"),
        Index("ix_claims_lines_lob_market", "lob", "market"),
        Index("ix_claims_lines_service_category", "service_category"),
        # Unique constraint on tenant + claim_line_id
        UniqueConstraint('tenant_id', 'claim_line_id', name='uq_claims_lines_tenant_claim_line'),
    )
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Primary Keys & Identifiers
    claim_id = Column(String, nullable=False, index=True)
    claim_line_id = Column(String, nullable=False, index=True)
    member_id = Column(String, nullable=False, index=True)
    provider_id = Column(String, nullable=False, index=True)
    
    # Temporal Fields (ix_claims_lines_service_date is in __table_args__)
    service_date = Column(Date, nullable=False)
    paid_date = Column(Date, nullable=True)
    adjudication_date = Column(Date, nullable=True)
    
    # Line of Business & Market
    lob = Column(String, nullable=False, index=True)
    market = Column(String, nullable=False, index=True)
    
    # Service Coding
    cpt_code = Column(String, nullable=True)
    hcpcs_code = Column(String, nullable=True)
    drg_code = Column(String, nullable=True)
    icd10_diagnosis_codes = Column(ARRAY(String), nullable=True)  # Array of strings
    icd10_procedure_codes = Column(ARRAY(String), nullable=True)  # Array of strings
    
    # Service Classification (ix_claims_lines_service_category is in __table_args__)
    service_category = Column(String, nullable=False)
    place_of_service = Column(String, nullable=False)
    
    # Utilization Metrics
    units = Column(Numeric(10, 2), nullable=False)
    
    # Financial Fields
    allowed_amount = Column(Numeric(12, 2), nullable=False)
    paid_amount = Column(Numeric(12, 2), nullable=False)
    member_cost_share = Column(Numeric(12, 2), nullable=False, default=0)
    
    # Network & Authorization
    in_network = Column(Boolean, nullable=False, default=True)
    requires_prior_auth = Column(Boolean, nullable=False, default=False)
    prior_auth_approved = Column(Boolean, nullable=True)
    prior_auth_id = Column(String, nullable=True)
    
    # Site-of-Care Information
    facility_type = Column(String, nullable=True)
    system_affiliation = Column(String, nullable=True)
    
    # Additional Context
    rendering_provider_id = Column(String, nullable=True)
    billing_provider_id = Column(String, nullable=True)
    referring_provider_id = Column(String, nullable=True)
    
    # Lineage & Metadata (from CanonicalBase)
    source_system = Column(String, nullable=False)
    source_file_id = Column(String, nullable=False)
    ingestion_id = Column(PGUUID(as_uuid=True), nullable=False)
    record_hash = Column(String, nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class EnrollmentRecordDB(Base):
    """Database model for EnrollmentRecord canonical data"""
    __tablename__ = "enrollment_records"
    __table_args__ = (
        Index("ix_enrollment_tenant_member", "tenant_id", "member_id"),
        Index("ix_enrollment_tenant_month", "tenant_id", "enrollment_month"),
        Index("ix_enrollment_lob_market", "lob", "market"),
        # Unique constraint on tenant + member_id + enrollment_month
        UniqueConstraint('tenant_id', 'member_id', 'enrollment_month', name='uq_enrollment_tenant_member_month'),
    )
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Primary Keys & Identifiers
    member_id = Column(String, nullable=False, index=True)
    enrollment_month = Column(Date, nullable=False, index=True)
    
    # Line of Business & Market
    lob = Column(String, nullable=False, index=True)
    market = Column(String, nullable=False, index=True)
    
    # Demographics
    age_band = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    risk_score = Column(Numeric(10, 4), nullable=False)
    
    # Network & Coverage
    network_tier = Column(String, nullable=False)
    enrolled_flag = Column(Boolean, nullable=False, default=True)
    
    # Enrollment Status
    enrollment_start_date = Column(Date, nullable=True)
    enrollment_end_date = Column(Date, nullable=True)
    
    # Additional Context
    product_type = Column(String, nullable=True)
    segment = Column(String, nullable=True)
    
    # Lineage & Metadata (from CanonicalBase)
    source_system = Column(String, nullable=False)
    source_file_id = Column(String, nullable=False)
    ingestion_id = Column(PGUUID(as_uuid=True), nullable=False)
    record_hash = Column(String, nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ProviderRecordDB(Base):
    """Database model for ProviderRecord canonical data"""
    __tablename__ = "provider_records"
    __table_args__ = (
        Index("ix_provider_tenant_provider", "tenant_id", "provider_id"),
        Index("ix_provider_npi", "npi"),
        Index("ix_provider_market", "market"),
        Index("ix_provider_network_status", "network_status"),
        # Unique constraint on tenant + provider_id + effective_date
        UniqueConstraint('tenant_id', 'provider_id', 'effective_date', name='uq_provider_tenant_provider_effective'),
    )
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Primary Keys & Identifiers (ix_provider_npi in __table_args__)
    provider_id = Column(String, nullable=False, index=True)
    npi = Column(String, nullable=True)
    
    # Provider Classification
    provider_type = Column(String, nullable=False)
    specialty = Column(String, nullable=True)
    facility_type = Column(String, nullable=True)
    
    # Geographic & Market (ix_provider_market in __table_args__)
    market = Column(String, nullable=False)
    state = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    
    # Network Information (ix_provider_network_status in __table_args__)
    network_status = Column(String, nullable=False)
    effective_date = Column(Date, nullable=False, index=True)
    termination_date = Column(Date, nullable=True)
    
    # System Affiliation
    system_affiliation = Column(String, nullable=True)
    system_id = Column(String, nullable=True)
    
    # Additional Context
    provider_name = Column(String, nullable=True)
    tax_id = Column(String, nullable=True)
    
    # Lineage & Metadata (from CanonicalBase)
    source_system = Column(String, nullable=False)
    source_file_id = Column(String, nullable=False)
    ingestion_id = Column(PGUUID(as_uuid=True), nullable=False)
    record_hash = Column(String, nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

