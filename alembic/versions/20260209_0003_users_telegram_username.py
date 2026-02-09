"""Add optional telegram_username to users for nickname-based master assignment

Revision ID: 20260209_0003
Revises: 20260209_0002
Create Date: 2026-02-09
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260209_0003"
down_revision = "20260209_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("telegram_username", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "telegram_username")
