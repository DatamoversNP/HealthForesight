"""Job schedule registry + occurrence ledger (enterprise scheduling).

Revision ID: 014
Revises: 013

STAGING_ONLY until authorized. Do not apply to Dec4 demo database
(demo must stay at 012 unless separately approved).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "014_job_schedules"
down_revision = "013_analytical_jobs_outbox"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("schedule_id", sa.String(), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_type", sa.String(), nullable=False),
        sa.Column("target_reference", sa.String(), nullable=False),
        sa.Column("schedule_expression", sa.String(), nullable=True),
        sa.Column("timezone", sa.String(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("trigger_kind", sa.String(), nullable=False),
        sa.Column("effective_start", sa.DateTime(), nullable=True),
        sa.Column("effective_end", sa.DateTime(), nullable=True),
        sa.Column("next_due_at", sa.DateTime(), nullable=True),
        sa.Column("misfire_policy", sa.String(), nullable=False),
        sa.Column("overlap_policy", sa.String(), nullable=False),
        sa.Column("retry_policy_json", sa.JSON(), nullable=True),
        sa.Column("execution_budget_s", sa.Integer(), nullable=False, server_default="3600"),
        sa.Column("required_data_watermark", sa.String(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("configuration_version", sa.String(), nullable=False),
        sa.Column("workload_class", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("schedule_id"),
    )
    op.create_index("ix_job_schedules_tenant_id", "job_schedules", ["tenant_id"])
    op.create_index("ix_job_schedules_next_due_at", "job_schedules", ["next_due_at"])
    op.create_index("ix_job_schedules_enabled", "job_schedules", ["enabled"])

    op.create_table(
        "job_schedule_occurrences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("occurrence_id", sa.String(), nullable=False),
        sa.Column("schedule_id", sa.String(), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("occurrence_key", sa.String(), nullable=False),
        sa.Column("configuration_version", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("due_at_utc", sa.DateTime(), nullable=False),
        sa.Column("data_watermark_satisfied", sa.Boolean(), nullable=True),
        sa.Column("analytical_job_id", sa.String(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "schedule_id",
            "occurrence_key",
            "configuration_version",
            name="uq_schedule_occurrence_identity",
        ),
        sa.UniqueConstraint("occurrence_id"),
    )
    op.create_index("ix_job_schedule_occurrences_status", "job_schedule_occurrences", ["status"])


def downgrade() -> None:
    op.drop_table("job_schedule_occurrences")
    op.drop_table("job_schedules")
