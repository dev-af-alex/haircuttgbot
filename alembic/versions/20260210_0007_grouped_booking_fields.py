"""Add grouped-booking participant fields and organizer ownership

Revision ID: 20260210_0007
Revises: 20260210_0006
Create Date: 2026-02-10
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260210_0007"
down_revision = "20260210_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("bookings", "client_user_id", existing_type=sa.Integer(), nullable=True)
    op.add_column("bookings", sa.Column("organizer_user_id", sa.Integer(), nullable=True))
    op.add_column("bookings", sa.Column("booking_group_key", sa.String(length=64), nullable=True))
    op.create_foreign_key(
        "fk_bookings_organizer_user_id_users",
        "bookings",
        "users",
        ["organizer_user_id"],
        ["id"],
    )
    op.create_index(
        "ix_bookings_organizer_status_slot_start",
        "bookings",
        ["organizer_user_id", "status", "slot_start"],
    )
    op.create_index(
        "ix_bookings_booking_group_key",
        "bookings",
        ["booking_group_key"],
    )


def downgrade() -> None:
    op.drop_index("ix_bookings_booking_group_key", table_name="bookings")
    op.drop_index("ix_bookings_organizer_status_slot_start", table_name="bookings")
    op.drop_constraint("fk_bookings_organizer_user_id_users", "bookings", type_="foreignkey")
    op.drop_column("bookings", "booking_group_key")
    op.drop_column("bookings", "organizer_user_id")
    op.alter_column("bookings", "client_user_id", existing_type=sa.Integer(), nullable=False)
