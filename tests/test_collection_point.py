import pytest
from models import CollectionPoint, AccountStatus
from tests.helpers import column, foreign_key_targets, relationship_names


@pytest.mark.parametrize(
    "name",
    [
        "collection_point_id",
        "cooperative_admin_id",
        "collection_name",
        "location",
        "status",
        "created_at",
    ],
)
def test_collection_point_columns_exist(name):
    assert name in CollectionPoint.__table__.columns


@pytest.mark.parametrize(
    "name",
    [
        "collection_point_id",
        "cooperative_admin_id",
        "collection_name",
        "location",
        "status",
        "created_at",
    ],
)
def test_collection_point_required_columns(name):
    assert column(CollectionPoint, name).nullable is False


def test_collection_point_owner_references_users():
    assert foreign_key_targets(CollectionPoint, "cooperative_admin_id") == {"users.user_id"}


def test_collection_point_default_status():
    assert CollectionPoint.status.default.arg == AccountStatus.ACTIVE


@pytest.mark.parametrize(
    "name",
    [
        "cooperative_admin",
        "farmers",
        "agent_assignments",
        "weighing_devices",
        "produce_records",
        "tasks",
    ],
)
def test_collection_point_relationships(name):
    assert name in relationship_names(CollectionPoint)


def test_collection_point_has_no_cooperative_id():
    assert "cooperative_id" not in CollectionPoint.__table__.columns
