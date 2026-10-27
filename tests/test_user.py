import pytest
from models import User, UserRole, AccountStatus
from tests.helpers import (
    column,
    constraint_names,
    foreign_key_targets,
    relationship_names,
)


@pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.AGENT, UserRole.FARMER])
def test_supported_user_roles(role):
    user = User(first_name="A", last_name="B", role=role)
    assert user.role == role


@pytest.mark.parametrize(
    "name",
    [
        "first_name",
        "last_name",
        "role",
        "status",
        "user_id",
        "created_at",
        "email",
        "phone_number",
        "id_number",
        "location",
        "cooperative_name",
        "cooperative_location",
        "collection_point_id",
        "registered_by_user_id",
        "password_hash",
    ],
)
def test_user_columns_exist(name):
    assert name in User.__table__.columns


@pytest.mark.parametrize("name", ["first_name", "last_name", "role", "status", "user_id", "created_at"])
def test_user_core_columns_are_required(name):
    assert column(User, name).nullable is False


@pytest.mark.parametrize(
    "name",
    [
        "email",
        "phone_number",
        "id_number",
        "location",
        "cooperative_name",
        "cooperative_location",
        "collection_point_id",
        "registered_by_user_id",
        "password_hash",
    ],
)
def test_role_specific_user_fields_can_be_null(name):
    assert column(User, name).nullable is True


def test_user_email_unique_constraint_exists():
    assert "uq_users_email" in constraint_names(User)


def test_user_phone_unique_constraint_exists():
    assert "uq_users_phone_number" in constraint_names(User)


def test_user_id_number_unique_constraint_exists():
    assert "uq_users_id_number" in constraint_names(User)


def test_user_status_default_is_active():
    assert User.status.default.arg == AccountStatus.ACTIVE


def test_user_default_role_is_agent():
    assert User.role.default.arg == UserRole.AGENT


@pytest.mark.parametrize(
    "name",
    [
        "registered_by",
        "registered_users",
        "farmer_collection_point",
        "managed_collection_points",
        "agent_assignments",
        "assignments_made",
        "produce_records",
        "farmer_produce_records",
        "created_prices",
        "initiated_payments",
        "farmer_payments",
        "approved_payments",
        "reviewed_messages",
        "farmer_messages",
        "created_tasks",
        "assigned_tasks",
        "audit_logs",
    ],
)
def test_user_relationships_exist(name):
    assert name in relationship_names(User)


def test_user_table_is_plural():
    assert User.__tablename__ == "users"


def test_user_role_enum_contains_farmer():
    assert UserRole.FARMER.value == "farmer"


def test_user_role_enum_contains_admin():
    assert UserRole.ADMIN.value == "admin"


def test_user_role_enum_contains_agent():
    assert UserRole.AGENT.value == "agent"


def test_user_primary_key_is_uuid():
    assert User.__table__.primary_key.columns.keys() == ["user_id"]
