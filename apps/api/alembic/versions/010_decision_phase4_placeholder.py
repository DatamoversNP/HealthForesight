"""Placeholder: Azure DBs may report revision 010_decision_phase4 from a forked migration tree.

This repo's linear chain ends at 007_user_auth_source in source control; production DBs stamped
with 010_decision_phase4 would otherwise break Alembic (revision not found). This no-op
re-attaches that revision so ``alembic upgrade head`` and local tooling work.

If your database was never at 010_decision_phase4, Alembic will not apply this unless you
stamp or migrate through it.
"""
revision = "010_decision_phase4"
down_revision = "007_user_auth_source"
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
