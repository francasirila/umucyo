from models.payment_transaction import PaymentTransaction


def test_payment_transaction_table_name():
    assert PaymentTransaction.__tablename__ == "payment_transaction"


def test_payment_transaction_has_expected_columns():
    expected = [
        "payment_transaction_id",
        "farmer_id",
        "user_id",
        "produce_price_id",
        "provider",
        "quantity",
        "amount",
        "transaction_reference",
        "failure_reason",
        "status",
        "approved_at",
        "approved_by",
        "payment_date",
    ]
    assert expected == [column.name for column in PaymentTransaction.__table__.columns if column.name in expected]
    assert set(expected).issubset(set(PaymentTransaction.__table__.columns.keys()))


def test_payment_transaction_has_primary_key():
    assert PaymentTransaction.__table__.primary_key.columns
