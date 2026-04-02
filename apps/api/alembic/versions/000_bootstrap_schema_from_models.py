"""Bootstrap full schema from SQLAlchemy models (empty PostgreSQL).

Revision ID: 000_bootstrap
Revises:
Create Date: 2026-03-30

Historically, migration 001 assumed tenants/policies/users already existed (from
runtime create_all). Fresh Azure databases only ran Alembic and failed on 001.
This revision creates all ORM tables with correct FK order before 001.
"""
from alembic import op
import sqlalchemy as sa

revision = "000_bootstrap"
down_revision = None
branch_labels = None
depends_on = None


def _ensure_models_registered():
    from uepi_api.database import Base
    import uepi_api.models as models_pkg

    for name in models_pkg.__all__:
        getattr(models_pkg, name)
    return Base


def upgrade():
    bind = op.get_bind()

    # Production DBs often have schema from app init (or partial bootstrap) while
    # alembic_version is still empty. create_all then duplicates indexes. Skip if
    # any known application table already exists (not only tenants — some DBs may
    # have claims/canonical data without a full tenant row yet).
    if bind.execute(
        sa.text(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = ANY (ARRAY[
                'tenants', 'users', 'roles', 'policies',
                'claims_lines', 'enrollment_records', 'provider_records',
                'analyses', 'alembic_version'
              ])
            LIMIT 1
            """
        )
    ).scalar():
        return

    Base = _ensure_models_registered()
    Base.metadata.create_all(bind=bind, checkfirst=True)


def downgrade():
    bind = op.get_bind()
    Base = _ensure_models_registered()
    Base.metadata.drop_all(bind=bind)
