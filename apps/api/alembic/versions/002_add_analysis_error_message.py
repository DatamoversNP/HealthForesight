"""Add error_message to analyses

Revision ID: 002_analysis_error
Revises: 001_file_storage
Create Date: 2025-02-08

"""
from alembic import op

revision = '002_analysis_error'
down_revision = '001_file_storage'
branch_labels = None
depends_on = None


def upgrade():
    # Idempotent: add column only if it does not exist (PostgreSQL)
    op.execute("""
        DO $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'analyses' AND column_name = 'error_message'
          ) THEN
            ALTER TABLE analyses ADD COLUMN error_message TEXT;
          END IF;
        END $$;
    """)


def downgrade():
    op.drop_column('analyses', 'error_message')
