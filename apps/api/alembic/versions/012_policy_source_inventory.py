"""Policy source inventory + document provenance (authoritative ingestion scaffold).

Revision ID: 012
Revises: 011
Create Date: 2026-11-03

Additive only — does not alter existing policies/baselines/observations.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "012_policy_source_inventory"
down_revision = "011_perf_claims_obs_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "policy_source_documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("family_id", sa.String(), nullable=False, index=True),
        sa.Column("authority", sa.String(), nullable=False),
        sa.Column("source_document_id", sa.String(), nullable=False),
        sa.Column("source_version", sa.String(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("program", sa.String(), nullable=True),
        sa.Column("jurisdiction", sa.String(), nullable=True),
        sa.Column("state", sa.String(), nullable=True),
        sa.Column("effective_start", sa.DateTime(), nullable=True),
        sa.Column("effective_end", sa.DateTime(), nullable=True),
        sa.Column("document_relationships_json", JSONB(), nullable=True),
        sa.Column("raw_payload_json", JSONB(), nullable=True),
        sa.Column("ingest_batch_id", sa.String(), nullable=True, index=True),
        sa.Column("content_hash", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "tenant_id",
            "family_id",
            "source_document_id",
            "source_version",
            name="uq_policy_source_doc_version",
        ),
    )
    op.create_table(
        "policy_source_inventory",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("family_id", sa.String(), nullable=False, index=True),
        sa.Column("scope_declaration_json", JSONB(), nullable=False),
        sa.Column("discovered_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ingested_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("excluded_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("inaccessible_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("adapter_status", sa.String(), nullable=False),
        sa.Column("last_reconciled_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("tenant_id", "family_id", name="uq_policy_source_inventory_family"),
    )
    op.create_table(
        "policy_source_links",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("policy_id", UUID(as_uuid=True), sa.ForeignKey("policies.id"), nullable=False, index=True),
        sa.Column("source_document_id", UUID(as_uuid=True), sa.ForeignKey("policy_source_documents.id"), nullable=False, index=True),
        sa.Column("link_role", sa.String(), nullable=False),  # DEFINITION / SUPERSEDES / ARTICLE_OF / ADAPTATION_OF
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("policy_id", "source_document_id", "link_role", name="uq_policy_source_link"),
    )


def downgrade() -> None:
    op.drop_table("policy_source_links")
    op.drop_table("policy_source_inventory")
    op.drop_table("policy_source_documents")
