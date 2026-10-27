from models.produce_record import ProduceRecord


def test_produce_record_table_name():
    assert ProduceRecord.__tablename__ == "produce_record"


def test_produce_record_has_expected_columns():
    expected = [
        "produce_record_id",
        "cooperative_id",
        "produce_price_id",
        "farmer_id",
        "device_id",
        "payment_transaction_id",
        "collection_point_id",
        "delivery_status",
        "user_id",
        "gross_weight_kg",
        "rejected_weight_kg",
        "accepted_weight_kg",
        "agent_notes",
        "amount",
        "recorded_at",
    ]
    assert expected == [column.name for column in ProduceRecord.__table__.columns if column.name in expected]
    assert set(expected).issubset(set(ProduceRecord.__table__.columns.keys()))


def test_produce_record_has_primary_key():
    assert ProduceRecord.__table__.primary_key.columns
