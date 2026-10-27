import pytest
from models import PaymentTransaction, PaymentStatus
from tests.helpers import column, foreign_key_targets, relationship_names


@pytest.mark.parametrize(
    "name",
    [
        "payment_transaction_id",
        "farmer_id",
        "user_id",
        "provider",
        "period_start",
        "period_end",
        "quantity",
        "amount",
        "transaction_reference",
        "failure_reason",
        "status",
        "approved_at",
        "approved_by",
        "payment_date",
    ],
)
def test_payment_columns_exist(name):
    assert name in PaymentTransaction.__table__.columns


@pytest.mark.parametrize(
    "name",
    [
        "payment_transaction_id",
        "farmer_id",
        "user_id",
        "provider",
        "period_start",
        "period_end",
        "quantity",
        "amount",
        "transaction_reference",
        "status",
    ],
)
def test_payment_required_columns(name):
    assert column(PaymentTransaction, name).nullable is False


@pytest.mark.parametrize("name", ["failure_reason", "approved_at", "approved_by", "payment_date"])
def test_payment_optional_columns(name):
    assert column(PaymentTransaction, name).nullable is True


@pytest.mark.parametrize("name", ["farmer_id", "user_id", "approved_by"])
def test_payment_user_foreign_keys(name):
    assert foreign_key_targets(PaymentTransaction, name) == {"users.user_id"}


@pytest.mark.parametrize("name", ["ck_payment_period_valid", "ck_payment_quantity_nonnegative", "ck_payment_amount_positive"])
def test_payment_constraints_exist(name):
    pass


@pytest.mark.parametrize("name", ["farmer", "initiated_by", "approved_by_user", "produce_records"])
def test_payment_relationships_exist(name):
    assert name in relationship_names(PaymentTransaction)


def test_payment_default_status():
    assert PaymentTransaction.status.default.arg == PaymentStatus.PENDING


def test_payment_default_provider():
    assert PaymentTransaction.provider.default.arg == "Flutterwave"


def test_payment_has_no_cooperative_id():
    assert "cooperative_id" not in PaymentTransaction.__table__.columns
