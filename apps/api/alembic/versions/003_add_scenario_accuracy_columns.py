"""Add scenario_accuracy columns (linked_policy_id, observation_id, etc.)

Revision ID: 003_scenario_accuracy_cols
Revises: 002_analysis_error
Create Date: 2025-02-09

"""
from alembic import op
import sqlalchemy as sa

revision = '003_scenario_accuracy_cols'
down_revision = '002_analysis_error'
branch_labels = None
depends_on = None


def _column_exists(conn, table: str, column: str) -> bool:
    r = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = :t AND column_name = :c"
    ), {"t": table, "c": column})
    return r.scalar() is not None


def upgrade():
    conn = op.get_bind()
    cols = [
        ("linked_policy_id", "ALTER TABLE scenario_accuracy ADD COLUMN linked_policy_id UUID REFERENCES policies(id) ON DELETE SET NULL"),
        ("linked_at", "ALTER TABLE scenario_accuracy ADD COLUMN linked_at TIMESTAMP WITHOUT TIME ZONE"),
        ("metadata_json", "ALTER TABLE scenario_accuracy ADD COLUMN metadata_json JSONB"),
        ("observation_id", "ALTER TABLE scenario_accuracy ADD COLUMN observation_id UUID"),
        ("overall_accuracy_pct", "ALTER TABLE scenario_accuracy ADD COLUMN overall_accuracy_pct DOUBLE PRECISION"),
        ("utilization_accuracy_pct", "ALTER TABLE scenario_accuracy ADD COLUMN utilization_accuracy_pct DOUBLE PRECISION"),
        ("cost_accuracy_pct", "ALTER TABLE scenario_accuracy ADD COLUMN cost_accuracy_pct DOUBLE PRECISION"),
    ]
    for col_name, sql in cols:
        if not _column_exists(conn, "scenario_accuracy", col_name):
            op.execute(sa.text(sql))


def downgrade():
    for col in ["cost_accuracy_pct", "utilization_accuracy_pct", "overall_accuracy_pct", "observation_id", "metadata_json", "linked_at", "linked_policy_id"]:
        try:
            op.drop_column("scenario_accuracy", col)
        except Exception:
            pass
