from models.farmer import Farmer


def test_farmer_table_name():
    assert Farmer.__tablename__ == "farmer"


def test_farmer_has_expected_columns():
    expected = ["user_id", "collection_point_id", "registered_by_user_id", "phone_number"]
    assert expected == [column.name for column in Farmer.__table__.columns if column.name in expected]
    assert set(expected).issubset(set(Farmer.__table__.columns.keys()))


def test_farmer_has_primary_key():
    assert Farmer.__table__.primary_key.columns
