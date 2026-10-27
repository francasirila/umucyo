from models.user import User


def test_user_table_name():
    assert User.__tablename__ == "users"


def test_user_has_expected_columns():
    expected = [
        "user_id",
        "first_name",
        "last_name",
        "created_at",
        "status",
        "user_type",
    ]
    assert expected == [column.name for column in User.__table__.columns if column.name in expected]
    assert set(expected).issubset(set(User.__table__.columns.keys()))


def test_user_has_primary_key():
    assert User.__table__.primary_key.columns
