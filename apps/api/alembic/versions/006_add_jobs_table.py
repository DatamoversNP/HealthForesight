"""Add jobs table for daily job tracking

Revision ID: 006_jobs_table
Revises: 005_analytics_runs_verdict
Create Date: 2025-03-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '006_jobs_table'
down_revision = '005_analytics_runs_verdict'
branch_labels = None
depends_on = None


def _table_exists(conn, table: str) -> bool:
    r = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.tables WHERE table_name = :t"
    ), {"t": table})
    return r.scalar() is not None


def upgrade():
    conn = op.get_bind()
    if not _table_exists(conn, "jobs"):
        op.create_table(
            'jobs',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('job_id', sa.String(), nullable=False),
            sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
            sa.Column('job_type', sa.String(), nullable=False),
            sa.Column('status', sa.String(), nullable=False, server_default='PENDING'),
            sa.Column('message', sa.Text(), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('metadata_json', JSONB(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index('ix_jobs_job_id', 'jobs', ['job_id'], unique=True)
        op.create_index('ix_jobs_tenant_id', 'jobs', ['tenant_id'])
        op.create_index('ix_jobs_status', 'jobs', ['status'])


def downgrade():
    conn = op.get_bind()
    if _table_exists(conn, "jobs"):
        op.drop_index('ix_jobs_status', 'jobs')
        op.drop_index('ix_jobs_tenant_id', 'jobs')
        op.drop_index('ix_jobs_job_id', 'jobs')
        op.drop_table('jobs')
