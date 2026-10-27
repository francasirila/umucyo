from models.task import Task


def test_task_table_name():
    assert Task.__tablename__ == "task"


def test_task_has_expected_columns():
    expected = [
        "task_id",
        "cooperative_id",
        "created_by_user_id",
        "assigned_to_user_id",
        "collection_point_id",
        "message_id",
        "description",
        "priority",
        "created_at",
        "status",
        "completed_at",
    ]
    assert expected == [column.name for column in Task.__table__.columns if column.name in expected]
    assert set(expected).issubset(set(Task.__table__.columns.keys()))


def test_task_has_primary_key():
    assert Task.__table__.primary_key.columns
