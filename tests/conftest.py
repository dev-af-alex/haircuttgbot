from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _set_test_business_timezone(monkeypatch: pytest.MonkeyPatch) -> None:
    # Keep existing tests deterministic unless a test explicitly overrides this value.
    monkeypatch.setenv("BUSINESS_TIMEZONE", "UTC")
