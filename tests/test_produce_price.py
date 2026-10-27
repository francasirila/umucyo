import pytest
from models import ProducePrice
from tests.helpers import (
    column,
    constraint_names,
    foreign_key_targets,
    relationship_names,
)


@pytest.mark.parametrize(
    "name",
    [
        "produce_price_id",
        "cooperative_admin_id",
        "unit",
        "price_per_unit",
        "effective_from",
        "effective_to",
        "created_by_user_id",
        "created_at",
    ],
)
def test_price_columns_exist(name):
    assert name in ProducePrice.__table__.columns


@pytest.mark.parametrize(
    "name",
    [
        "produce_price_id",
        "cooperative_admin_id",
        "unit",
        "price_per_unit",
        "effective_from",
        "created_by_user_id",
        "created_at",
    ],
)
def test_price_required_columns(name):
    assert column(ProducePrice, name).nullable is False


def test_price_effective_to_is_optional():
    assert column(ProducePrice, "effective_to").nullable is True


@pytest.mark.parametrize("name", ["cooperative_admin_id", "created_by_user_id"])
def test_price_user_foreign_keys(name):
    assert foreign_key_targets(ProducePrice, name) == {"users.user_id"}


@pytest.mark.parametrize("name", ["ck_produce_price_nonnegative", "ck_produce_price_valid_period"])
def test_price_constraints_exist(name):
    assert name in constraint_names(ProducePrice)


@pytest.mark.parametrize("name", ["cooperative_admin", "created_by", "produce_records"])
def test_price_relationships_exist(name):
    assert name in relationship_names(ProducePrice)


def test_price_default_unit_is_kg():
    assert ProducePrice.unit.default.arg == "kg"


def test_price_has_no_cooperative_id():
    assert "cooperative_id" not in ProducePrice.__table__.columns
