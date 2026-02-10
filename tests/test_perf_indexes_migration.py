from pathlib import Path


def test_perf_indexes_migration_declares_expected_revision_chain() -> None:
    path = Path("alembic/versions/20260210_0006_booking_query_perf_indexes.py")
    content = path.read_text(encoding="utf-8")

    assert 'revision = "20260210_0006"' in content
    assert 'down_revision = "20260210_0005"' in content


def test_perf_indexes_migration_contains_hotspot_indexes() -> None:
    path = Path("alembic/versions/20260210_0006_booking_query_perf_indexes.py")
    content = path.read_text(encoding="utf-8")

    expected_index_names = [
        "ix_bookings_master_status_slot_start",
        "ix_bookings_client_status_slot_start",
        "ix_bookings_active_master_slot_window",
        "ix_availability_blocks_master_start_end",
        "ix_availability_blocks_dayoff_master_start_end",
        "ix_booking_reminders_pending_due_at_id",
        "ix_users_lower_telegram_username",
    ]
    for index_name in expected_index_names:
        assert index_name in content
