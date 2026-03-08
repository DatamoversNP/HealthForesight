"""Lineage and run history models"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String
from sqlalchemy import UUID as GenericUUID
# Use generic UUID that works with all databases
PGUUID = GenericUUID
from sqlalchemy.orm import relationship

from uepi_api.database import Base


class DatasetSnapshot(Base):
    """Dataset snapshot (data coverage at point in time)"""
    __tablename__ = "dataset_snapshots"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    coverage_json = Column(JSON, nullable=False)  # {year: {month: {lob: {market: count}}}}
    source_files_manifest_uri = Column(String, nullable=True)  # S3 URI to manifest
    
    # AnalysisRun references this via snapshot_id foreign key


# Note: AnalysisRun for lineage is the same as in analysis.py
# We'll use the AnalysisRun from analysis.py and link it to DatasetSnapshot

