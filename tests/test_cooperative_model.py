from models.cooperative import Cooperative


def test_cooperative_table_name():
    assert Cooperative.__tablename__ == "cooperative"


def test_cooperative_has_expected_columns():
    expected = ["cooperative_id", "cooperative_name", "email", "created_at", "status"]
    assert expected == [column.name for column in Cooperative.__table__.columns if column.name in expected]
    assert set(expected).issubset(set(Cooperative.__table__.columns.keys()))


def test_cooperative_has_primary_key():
    assert Cooperative.__table__.primary_key.columns
