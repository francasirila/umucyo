from models.message_log import MessageLog


def test_message_log_table_name():
    assert MessageLog.__tablename__ == "message_log"


def test_message_log_has_expected_columns():
    expected = [
        "message_id",
        "farmer_id",
        "direction",
        "channel",
        "message_type",
        "content",
        "category",
        "status",
        "sent_at",
        "reviewed_by",
        "received_at",
        "provider_message_id",
        "created_at",
    ]
    assert expected == [column.name for column in MessageLog.__table__.columns if column.name in expected]
    assert set(expected).issubset(set(MessageLog.__table__.columns.keys()))


def test_message_log_has_primary_key():
    assert MessageLog.__table__.primary_key.columns
