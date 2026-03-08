"""Data Quality models for storing quality reports and trust scores"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, Index
from sqlalchemy import UUID as GenericUUID
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from uepi_api.database import Base


class DataQualityReport(Base):
    """Data quality report stored in database"""
    __tablename__ = "data_quality_reports"
    __table_args__ = (
        Index("ix_data_quality_reports_tenant_created", "tenant_id", "created_at"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Overall scores
    overall_quality_score = Column(Float, nullable=False)  # 0-100
    trust_score = Column(Float, nullable=False)  # 0-100 - business-friendly trust indicator
    trust_level = Column(String, nullable=False)  # EXCELLENT, GOOD, FAIR, POOR, UNTRUSTWORTHY
    trust_recommendation = Column(Text, nullable=True)  # Business-friendly recommendation
    
    # Component scores
    completeness_score = Column(Float, nullable=False)
    validity_score = Column(Float, nullable=False)
    uniqueness_score = Column(Float, nullable=False)
    integrity_score = Column(Float, nullable=False)
    consistency_score = Column(Float, nullable=False)  # Cross-dataset consistency
    
    # Issue counts
    total_issues = Column(Integer, nullable=False, default=0)
    critical_issues = Column(Integer, nullable=False, default=0)
    high_issues = Column(Integer, nullable=False, default=0)
    medium_issues = Column(Integer, nullable=False, default=0)
    low_issues = Column(Integer, nullable=False, default=0)
    
    # Detailed report (JSON)
    report_json = Column(JSON, nullable=False)  # Full detailed report
    datasets_summary = Column(JSON, nullable=True)  # Summary per dataset
    issues_summary = Column(JSON, nullable=True)  # Grouped issues
    
    # Business-friendly summary
    executive_summary = Column(Text, nullable=True)  # Plain language summary
    key_concerns = Column(JSON, nullable=True)  # Top concerns for business users
    data_coverage = Column(JSON, nullable=True)  # Data coverage metrics
    
    # Metadata
    validation_started_at = Column(DateTime, nullable=True)
    validation_completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)


class DataQualityIssue(Base):
    """Individual data quality issues for detailed tracking"""
    __tablename__ = "data_quality_issues"
    __table_args__ = (
        Index("ix_data_quality_issues_report_severity", "report_id", "severity"),
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    report_id = Column(PGUUID(as_uuid=True), ForeignKey("data_quality_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Issue details
    issue_type = Column(String, nullable=False)  # COMPLETENESS, VALIDITY, UNIQUENESS, etc.
    severity = Column(String, nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    dataset = Column(String, nullable=True)  # CLAIMS_LINES, ENROLLMENT, PROVIDERS, CROSS_DATASET
    field_name = Column(String, nullable=True)
    
    # Issue description
    description = Column(Text, nullable=False)
    business_impact = Column(Text, nullable=True)  # Business-friendly impact description
    
    # Metrics
    affected_rows = Column(Integer, nullable=False, default=0)
    affected_percentage = Column(Float, nullable=True)
    
    # Sample data
    sample_values = Column(JSON, nullable=True)  # Sample problematic values
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    report = relationship("DataQualityReport", backref="issues")

