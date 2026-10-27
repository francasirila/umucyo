from models.cooperative_user import CooperativeUser


def test_cooperative_user_table_name():
    assert CooperativeUser.__tablename__ == "cooperative_user"


def test_cooperative_user_has_expected_columns():
    expected = ["user_id"]
    assert expected == [column.name for column in CooperativeUser.__table__.columns if column.name in expected]
    assert set(expected).issubset(set(CooperativeUser.__table__.columns.keys()))


def test_cooperative_user_has_primary_key():
    assert CooperativeUser.__table__.primary_key.columns
