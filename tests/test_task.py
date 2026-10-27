import pytest
from models import Task, TaskPriority, TaskStatus
from tests.helpers import (
    column,
    constraint_names,
    foreign_key_targets,
    relationship_names,
)


@pytest.mark.parametrize(
    "name",
    [
        "task_id",
        "created_by_user_id",
        "assigned_to_user_id",
        "collection_point_id",
        "message_id",
        "description",
        "priority",
        "created_at",
        "status",
        "completed_at",
    ],
)
def test_task_columns_exist(name):
    assert name in Task.__table__.columns


@pytest.mark.parametrize(
    "name",
    [
        "task_id",
        "created_by_user_id",
        "assigned_to_user_id",
        "description",
        "priority",
        "created_at",
        "status",
    ],
)
def test_task_required_columns(name):
    assert column(Task, name).nullable is False


@pytest.mark.parametrize("name", ["collection_point_id", "message_id", "completed_at"])
def test_task_optional_columns(name):
    assert column(Task, name).nullable is True


@pytest.mark.parametrize("name", ["created_by_user_id", "assigned_to_user_id"])
def test_task_user_foreign_keys(name):
    assert foreign_key_targets(Task, name) == {"users.user_id"}


def test_task_completion_constraint_exists():
    assert "ck_task_completion_timestamp" in constraint_names(Task)


@pytest.mark.parametrize("name", ["created_by", "assigned_to", "collection_point", "message"])
def test_task_relationships_exist(name):
    assert name in relationship_names(Task)


def test_task_default_priority():
    assert Task.priority.default.arg == TaskPriority.NORMAL


def test_task_default_status():
    assert Task.status.default.arg == TaskStatus.OPEN


def test_task_has_no_cooperative_id():
    assert "cooperative_id" not in Task.__table__.columns
