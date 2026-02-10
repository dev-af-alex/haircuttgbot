"""Add booking notification context fields and optional user phone

Revision ID: 20260210_0004
Revises: 20260209_0003
Create Date: 2026-02-10
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260210_0004"
down_revision = "20260209_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone_number", sa.String(length=32), nullable=True))
    op.add_column("bookings", sa.Column("manual_client_name", sa.String(length=160), nullable=True))
    op.add_column("bookings", sa.Column("client_username_snapshot", sa.String(length=64), nullable=True))
    op.add_column("bookings", sa.Column("client_phone_snapshot", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("bookings", "client_phone_snapshot")
    op.drop_column("bookings", "client_username_snapshot")
    op.drop_column("bookings", "manual_client_name")
    op.drop_column("users", "phone_number")
