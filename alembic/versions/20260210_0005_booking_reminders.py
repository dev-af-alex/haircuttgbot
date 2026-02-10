"""Add booking reminders table for 2-hour reminder workflow

Revision ID: 20260210_0005
Revises: 20260210_0004
Create Date: 2026-02-10
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260210_0005"
down_revision = "20260210_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "booking_reminders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id"), nullable=False, unique=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status IN ('pending', 'sent', 'skipped')", name="ck_booking_reminders_status"),
    )
    op.create_index("ix_booking_reminders_due_status", "booking_reminders", ["status", "due_at"])


def downgrade() -> None:
    op.drop_index("ix_booking_reminders_due_status", table_name="booking_reminders")
    op.drop_table("booking_reminders")
