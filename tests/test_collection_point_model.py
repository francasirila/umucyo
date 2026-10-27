from models.collection_point import CollectionPoint


def test_collection_point_table_name():
    assert CollectionPoint.__tablename__ == "collection_point"


def test_collection_point_has_expected_columns():
    expected = ["collection_point_id", "cooperative_id", "collection_name", "status", "created_at"]
    assert expected == [column.name for column in CollectionPoint.__table__.columns if column.name in expected]
    assert set(expected).issubset(set(CollectionPoint.__table__.columns.keys()))


def test_collection_point_has_primary_key():
    assert CollectionPoint.__table__.primary_key.columns
