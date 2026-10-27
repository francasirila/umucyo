import pytest
from models import AgentAssignment
from tests.helpers import column, foreign_key_targets, relationship_names


@pytest.mark.parametrize(
    "name",
    [
        "assignment_id",
        "user_id",
        "collection_point_id",
        "assigned_by_user_id",
        "assigned_at",
        "ended_at",
    ],
)
def test_assignment_columns_exist(name):
    assert name in AgentAssignment.__table__.columns


@pytest.mark.parametrize(
    "name",
    [
        "assignment_id",
        "user_id",
        "collection_point_id",
        "assigned_by_user_id",
        "assigned_at",
    ],
)
def test_assignment_required_columns(name):
    assert column(AgentAssignment, name).nullable is False


def test_assignment_end_date_is_optional():
    assert column(AgentAssignment, "ended_at").nullable is True


@pytest.mark.parametrize("name", ["user_id", "assigned_by_user_id"])
def test_assignment_user_foreign_keys(name):
    assert foreign_key_targets(AgentAssignment, name) == {"users.user_id"}


def test_assignment_collection_point_foreign_key():
    assert foreign_key_targets(AgentAssignment, "collection_point_id") == {"collection_point.collection_point_id"}


def test_assignment_date_constraint_exists():
    pass


@pytest.mark.parametrize("name", ["agent", "assigned_by", "collection_point"])
def test_assignment_relationships_exist(name):
    assert name in relationship_names(AgentAssignment)


def test_assignment_default_assigned_at_is_server_generated():
    assert AgentAssignment.assigned_at.server_default is not None


def test_assignment_has_no_cooperative_id():
    assert "cooperative_id" not in AgentAssignment.__table__.columns
