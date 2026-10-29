from datetime import datetime, timezone

from core.utils import ensure_aware, enum_value, utcnow
from models.enums import UserRole


def test_utcnow_is_timezone_aware():
    assert utcnow().tzinfo is not None


def test_ensure_aware_handles_none_naive_and_aware():
    naive = datetime(2025, 1, 1, 12, 0, 0)
    aware = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    assert ensure_aware(None) is None
    assert ensure_aware(naive).tzinfo == timezone.utc
    assert ensure_aware(aware) is aware


def test_enum_value_unwraps_enums_and_passes_plain_values():
    assert enum_value(UserRole.admin) == "admin"
    assert enum_value("agent") == "agent"
    assert enum_value(None) is None
