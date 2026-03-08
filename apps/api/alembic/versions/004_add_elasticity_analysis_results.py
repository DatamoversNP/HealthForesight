"""Add elasticity_analysis_results table

Revision ID: 004_elasticity_results
Revises: 003_scenario_accuracy_cols
Create Date: 2025-02-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '004_elasticity_results'
down_revision = '003_scenario_accuracy_cols'
branch_labels = None
depends_on = None


def _table_exists(conn, table: str) -> bool:
    r = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.tables WHERE table_name = :t"
    ), {"t": table})
    return r.scalar() is not None


def upgrade():
    conn = op.get_bind()
    if _table_exists(conn, "elasticity_analysis_results"):
        return
    op.create_table(
        'elasticity_analysis_results',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('analysis_id', UUID(as_uuid=True), sa.ForeignKey('analyses.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
        sa.Column('policy_id', UUID(as_uuid=True), sa.ForeignKey('policies.id'), nullable=True, index=True),
        sa.Column('result_data_json', JSONB, nullable=False),
        sa.Column('schema_version', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_elasticity_results_analysis', 'elasticity_analysis_results', ['analysis_id'])
    op.create_index('ix_elasticity_results_tenant', 'elasticity_analysis_results', ['tenant_id'])
    op.create_index('ix_elasticity_results_policy', 'elasticity_analysis_results', ['policy_id'])


def downgrade():
    op.drop_table('elasticity_analysis_results')
