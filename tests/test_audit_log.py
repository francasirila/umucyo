import pytest
from models import AuditLog
from tests.helpers import column, foreign_key_targets, relationship_names


@pytest.mark.parametrize(
    "name", ["audit_log_id", "user_id", "action", "entity_type", "entity_id", "old_values", "new_values", "created_at"]
)
def test_audit_columns_exist(name):
    assert name in AuditLog.__table__.columns


@pytest.mark.parametrize("name", ["audit_log_id", "action", "entity_type", "entity_id", "created_at"])
def test_audit_required_columns(name):
    assert column(AuditLog, name).nullable is False


@pytest.mark.parametrize("name", ["user_id", "old_values", "new_values"])
def test_audit_optional_columns(name):
    assert column(AuditLog, name).nullable is True


def test_audit_actor_references_users():
    assert foreign_key_targets(AuditLog, "user_id") == {"users.user_id"}


def test_audit_user_relationship_exists():
    assert "user" in relationship_names(AuditLog)


def test_audit_json_values_use_json_type():
    assert column(AuditLog, "old_values").type.__class__.__name__ == "JSON"
    assert column(AuditLog, "new_values").type.__class__.__name__ == "JSON"
