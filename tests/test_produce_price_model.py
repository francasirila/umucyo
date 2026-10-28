from models.produce_price import ProducePrice


def test_produce_price_table_name():
    assert ProducePrice.__tablename__ == "produce_price"


def test_produce_price_has_expected_columns():
    expected = [
        "produce_price_id",
        "cooperative_id",
        "unit",
        "price_per_unit",
        "effective_from",
        "effective_to",
        "created_by_user_id",
        "created_at",
    ]
    assert expected == [column.name for column in ProducePrice.__table__.columns if column.name in expected]
    assert set(expected).issubset(set(ProducePrice.__table__.columns.keys()))


def test_produce_price_has_primary_key():
    assert ProducePrice.__table__.primary_key.columns
