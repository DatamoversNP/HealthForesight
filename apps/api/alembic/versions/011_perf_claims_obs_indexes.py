"""Add composite indexes for page-load query paths (claims date windows, latest obs per policy).

Revision ID: 011_perf_claims_obs_indexes
Revises: 010_decision_phase4
Create Date: 2026-10-31

Safe / additive only. Uses CREATE INDEX CONCURRENTLY when possible so existing traffic
is not blocked by a long exclusive lock. Downgrade drops the new indexes only.
"""
from alembic import op
import sqlalchemy as sa

revision = "011_perf_claims_obs_indexes"
down_revision = "010_decision_phase4"
branch_labels = None
depends_on = None


def _index_exists(conn, index_name: str) -> bool:
    r = conn.execute(
        sa.text("SELECT 1 FROM pg_indexes WHERE indexname = :n"),
        {"n": index_name},
    )
    return r.scalar() is not None


def _table_exists(conn, table: str) -> bool:
    r = conn.execute(
        sa.text("SELECT 1 FROM information_schema.tables WHERE table_name = :t"),
        {"t": table},
    )
    return r.scalar() is not None


def upgrade() -> None:
    # CONCURRENTLY cannot run inside a transaction
    with op.get_context().autocommit_block():
        conn = op.get_bind()

        if _table_exists(conn, "claims_lines"):
            if not _index_exists(conn, "ix_claims_lines_tenant_service_date"):
                op.execute(
                    sa.text(
                        "CREATE INDEX CONCURRENTLY IF NOT EXISTS "
                        "ix_claims_lines_tenant_service_date "
                        "ON claims_lines (tenant_id, service_date)"
                    )
                )

        if _table_exists(conn, "observations"):
            if not _index_exists(conn, "ix_observations_tenant_policy_period_end"):
                op.execute(
                    sa.text(
                        "CREATE INDEX CONCURRENTLY IF NOT EXISTS "
                        "ix_observations_tenant_policy_period_end "
                        "ON observations (tenant_id, policy_id, observation_period_end DESC, computed_at DESC)"
                    )
                )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        conn = op.get_bind()
        for name in (
            "ix_observations_tenant_policy_period_end",
            "ix_claims_lines_tenant_service_date",
        ):
            if _index_exists(conn, name):
                op.execute(sa.text(f"DROP INDEX CONCURRENTLY IF EXISTS {name}"))
