"""Add auth_source and password_hash to users for AD + local user support

Revision ID: 007_user_auth_source
Revises: 006_jobs_table
Create Date: 2025-03-05

"""
from alembic import op
import sqlalchemy as sa

revision = '007_user_auth_source'
down_revision = '006_jobs_table'
branch_labels = None
depends_on = None


def _column_exists(conn, table: str, column: str) -> bool:
    r = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns WHERE table_name = :t AND column_name = :c"
    ), {"t": table, "c": column})
    return r.scalar() is not None


def upgrade():
    conn = op.get_bind()
    if not _column_exists(conn, "users", "auth_source"):
        op.add_column("users", sa.Column("auth_source", sa.String(32), nullable=True))
        op.execute(sa.text(
            "UPDATE users SET auth_source = CASE WHEN oidc_sub IS NOT NULL AND oidc_sub != '' THEN 'oidc' ELSE 'local' END"
        ))
    if not _column_exists(conn, "users", "password_hash"):
        op.add_column("users", sa.Column("password_hash", sa.String(255), nullable=True))


def downgrade():
    op.drop_column("users", "password_hash")
    op.drop_column("users", "auth_source")
