import pytest
from models import ProduceRecord
from tests.helpers import (
    column,
    constraint_names,
    foreign_key_targets,
    relationship_names,
)


@pytest.mark.parametrize(
    "name",
    [
        "produce_record_id",
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
    ],
)
def test_produce_record_columns_exist(name):
    assert name in ProduceRecord.__table__.columns


@pytest.mark.parametrize(
    "name",
    [
        "produce_record_id",
        "produce_price_id",
        "farmer_id",
        "device_id",
        "collection_point_id",
        "delivery_status",
        "user_id",
        "gross_weight_kg",
        "rejected_weight_kg",
        "accepted_weight_kg",
        "agent_notes",
        "amount",
        "recorded_at",
    ],
)
def test_produce_record_required_columns(name):
    assert column(ProduceRecord, name).nullable is False


def test_payment_transaction_reference_is_optional():
    assert column(ProduceRecord, "payment_transaction_id").nullable is True


@pytest.mark.parametrize(
    "name,target",
    [
        ("farmer_id", "users.user_id"),
        ("user_id", "users.user_id"),
        ("device_id", "weighing_device.device_id"),
        ("produce_price_id", "produce_price.produce_price_id"),
        ("collection_point_id", "collection_point.collection_point_id"),
        ("payment_transaction_id", "payment_transaction.payment_transaction_id"),
    ],
)
def test_produce_record_foreign_keys(name, target):
    assert foreign_key_targets(ProduceRecord, name) == {target}


@pytest.mark.parametrize(
    "name",
    [
        "ck_produce_gross_nonnegative",
        "ck_produce_rejected_valid",
        "ck_produce_accepted_valid",
        "ck_produce_weight_balance",
        "ck_produce_amount_nonnegative",
    ],
)
def test_produce_record_constraints_exist(name):
    assert name in constraint_names(ProduceRecord)


@pytest.mark.parametrize(
    "name",
    [
        "produce_price",
        "farmer",
        "device",
        "payment_transaction",
        "collection_point",
        "agent",
    ],
)
def test_produce_record_relationships_exist(name):
    assert name in relationship_names(ProduceRecord)


def test_produce_record_has_no_cooperative_id():
    assert "cooperative_id" not in ProduceRecord.__table__.columns
