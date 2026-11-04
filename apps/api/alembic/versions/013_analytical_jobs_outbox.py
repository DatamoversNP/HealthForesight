"""Durable analytical jobs + transactional outbox.

Revision ID: 013
Revises: 012
Create Date: 2026-11-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "013_analytical_jobs_outbox"
down_revision = "012_policy_source_inventory"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analytical_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", sa.String(), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_type", sa.String(), nullable=False),
        sa.Column("workload_class", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lease_owner", sa.String(), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(), nullable=True),
        sa.Column("queue_enqueued_at", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("error_category", sa.String(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("configuration_digest", sa.String(), nullable=True),
        sa.Column("dataset_snapshot_json", sa.JSON(), nullable=True),
        sa.Column("result_artifact_json", sa.JSON(), nullable=True),
        sa.Column("cancellation_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("job_id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index("ix_analytical_jobs_tenant_id", "analytical_jobs", ["tenant_id"])
    op.create_index("ix_analytical_jobs_status", "analytical_jobs", ["status"])
    op.create_index("ix_analytical_jobs_workload_class", "analytical_jobs", ["workload_class"])

    op.create_table(
        "job_outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", sa.String(), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("destination", sa.String(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_job_outbox_status", "job_outbox", ["status"])
    op.create_index("ix_job_outbox_job_id", "job_outbox", ["job_id"])


def downgrade() -> None:
    op.drop_table("job_outbox")
    op.drop_table("analytical_jobs")
