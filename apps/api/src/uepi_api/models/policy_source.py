"""Authoritative policy source inventory models (additive)."""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy import UUID as GenericUUID
from sqlalchemy.dialects.postgresql import JSONB

from uepi_api.database import Base

PGUUID = GenericUUID
JSONType = JSONB


class PolicySourceDocument(Base):
    __tablename__ = "policy_source_documents"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "family_id",
            "source_document_id",
            "source_version",
            name="uq_policy_source_doc_version",
        ),
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    family_id = Column(String, nullable=False, index=True)
    authority = Column(String, nullable=False)
    source_document_id = Column(String, nullable=False)
    source_version = Column(String, nullable=True)
    title = Column(Text, nullable=False)
    source_url = Column(Text, nullable=True)
    program = Column(String, nullable=True)
    jurisdiction = Column(String, nullable=True)
    state = Column(String, nullable=True)
    effective_start = Column(DateTime, nullable=True)
    effective_end = Column(DateTime, nullable=True)
    document_relationships_json = Column(JSONType, nullable=True)
    raw_payload_json = Column(JSONType, nullable=True)
    ingest_batch_id = Column(String, nullable=True, index=True)
    content_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class PolicySourceInventory(Base):
    __tablename__ = "policy_source_inventory"
    __table_args__ = (
        UniqueConstraint("tenant_id", "family_id", name="uq_policy_source_inventory_family"),
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    family_id = Column(String, nullable=False, index=True)
    scope_declaration_json = Column(JSONType, nullable=False)
    discovered_count = Column(Integer, nullable=False, default=0)
    ingested_count = Column(Integer, nullable=False, default=0)
    excluded_count = Column(Integer, nullable=False, default=0)
    inaccessible_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    adapter_status = Column(String, nullable=False)
    last_reconciled_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class PolicySourceLink(Base):
    __tablename__ = "policy_source_links"
    __table_args__ = (
        UniqueConstraint("policy_id", "source_document_id", "link_role", name="uq_policy_source_link"),
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id"), nullable=False, index=True)
    source_document_id = Column(
        PGUUID(as_uuid=True), ForeignKey("policy_source_documents.id"), nullable=False, index=True
    )
    link_role = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
