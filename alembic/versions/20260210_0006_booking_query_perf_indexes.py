"""Add performance indexes for booking and schedule query hotspots

Revision ID: 20260210_0006
Revises: 20260210_0005
Create Date: 2026-02-10
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260210_0006"
down_revision = "20260210_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_bookings_master_status_slot_start",
        "bookings",
        ["master_id", "status", "slot_start"],
    )
    op.create_index(
        "ix_bookings_client_status_slot_start",
        "bookings",
        ["client_user_id", "status", "slot_start"],
    )
    op.create_index(
        "ix_bookings_active_master_slot_window",
        "bookings",
        ["master_id", "slot_start", "slot_end"],
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "ix_availability_blocks_master_start_end",
        "availability_blocks",
        ["master_id", "start_at", "end_at"],
    )
    op.create_index(
        "ix_availability_blocks_dayoff_master_start_end",
        "availability_blocks",
        ["master_id", "start_at", "end_at"],
        postgresql_where=sa.text("block_type = 'day_off'"),
    )
    op.create_index(
        "ix_booking_reminders_pending_due_at_id",
        "booking_reminders",
        ["due_at", "id"],
        postgresql_where=sa.text("status = 'pending'"),
    )
    op.create_index(
        "ix_users_lower_telegram_username",
        "users",
        [sa.text("lower(telegram_username)")],
        unique=False,
        postgresql_where=sa.text("telegram_username IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_users_lower_telegram_username", table_name="users")
    op.drop_index("ix_booking_reminders_pending_due_at_id", table_name="booking_reminders")
    op.drop_index("ix_availability_blocks_dayoff_master_start_end", table_name="availability_blocks")
    op.drop_index("ix_availability_blocks_master_start_end", table_name="availability_blocks")
    op.drop_index("ix_bookings_active_master_slot_window", table_name="bookings")
    op.drop_index("ix_bookings_client_status_slot_start", table_name="bookings")
    op.drop_index("ix_bookings_master_status_slot_start", table_name="bookings")
