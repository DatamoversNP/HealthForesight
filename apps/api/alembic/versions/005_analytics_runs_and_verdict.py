"""Phase 1 & 2: analytics_runs table, run_id on baselines/observations, verdict columns on observations

Revision ID: 005_analytics_runs_verdict
Revises: 004_elasticity_results
Create Date: 2025-02-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '005_analytics_runs_verdict'
down_revision = '004_elasticity_results'
branch_labels = None
depends_on = None


def _table_exists(conn, table: str) -> bool:
    r = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.tables WHERE table_name = :t"
    ), {"t": table})
    return r.scalar() is not None


def _column_exists(conn, table: str, column: str) -> bool:
    r = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns WHERE table_name = :t AND column_name = :c"
    ), {"t": table, "c": column})
    return r.scalar() is not None


def upgrade():
    conn = op.get_bind()

    if not _table_exists(conn, "analytics_runs"):
        op.create_table(
            'analytics_runs',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
            sa.Column('run_type', sa.String(32), nullable=False),
            sa.Column('status', sa.String(32), nullable=False, server_default='RUNNING'),
            sa.Column('started_at', sa.DateTime(), nullable=False),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('input_refs_json', JSONB(), nullable=True),
            sa.Column('config_snapshot_json', JSONB(), nullable=True),
            sa.Column('output_refs_json', JSONB(), nullable=True),
            sa.Column('triggered_by_user_id', UUID(as_uuid=True), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_analytics_runs_tenant_id', 'analytics_runs', ['tenant_id'])
        op.create_index('ix_analytics_runs_tenant_type', 'analytics_runs', ['tenant_id', 'run_type'])
        op.create_index('ix_analytics_runs_status', 'analytics_runs', ['status'])
        op.create_index('ix_analytics_runs_started_at', 'analytics_runs', ['started_at'])

    if _table_exists(conn, "baselines") and not _column_exists(conn, "baselines", "analytics_run_id"):
        op.add_column('baselines', sa.Column('analytics_run_id', UUID(as_uuid=True), nullable=True))
        op.create_index('ix_baselines_analytics_run_id', 'baselines', ['analytics_run_id'])

    if _table_exists(conn, "observations") and not _column_exists(conn, "observations", "analytics_run_id"):
        op.add_column('observations', sa.Column('analytics_run_id', UUID(as_uuid=True), nullable=True))
        op.create_index('ix_observations_analytics_run_id', 'observations', ['analytics_run_id'])

    # Phase 2: verdict and recommendation on observations
    if _table_exists(conn, "observations") and not _column_exists(conn, "observations", "verdict_status"):
        op.add_column('observations', sa.Column('verdict_status', sa.String(32), nullable=True))
        op.add_column('observations', sa.Column('verdict_reason', sa.Text(), nullable=True))
        op.add_column('observations', sa.Column('recommendation', sa.Text(), nullable=True))
        op.add_column('observations', sa.Column('verdict_rule_version', sa.String(32), nullable=True))
        op.create_index('ix_observations_verdict_status', 'observations', ['verdict_status'])


def downgrade():
    conn = op.get_bind()
    if _table_exists(conn, "observations"):
        if _column_exists(conn, "observations", "verdict_rule_version"):
            op.drop_index('ix_observations_verdict_status', 'observations')
            op.drop_column('observations', 'verdict_rule_version')
            op.drop_column('observations', 'recommendation')
            op.drop_column('observations', 'verdict_reason')
            op.drop_column('observations', 'verdict_status')
        if _column_exists(conn, "observations", "analytics_run_id"):
            op.drop_index('ix_observations_analytics_run_id', 'observations')
            op.drop_column('observations', 'analytics_run_id')
    if _table_exists(conn, "baselines") and _column_exists(conn, "baselines", "analytics_run_id"):
        op.drop_index('ix_baselines_analytics_run_id', 'baselines')
        op.drop_column('baselines', 'analytics_run_id')
    if _table_exists(conn, "analytics_runs"):
        op.drop_table('analytics_runs')
