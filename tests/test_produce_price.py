from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException

from schemas.produce_price import ProducePriceCreate, ProducePriceUpdate
from services.produce_price import ProducePriceService


def test_get_produce_price(db_session, produce_graph):
    service = ProducePriceService(db_session)
    price = produce_graph.price

    result = service.get_produce_price(price.produce_price_id)

    assert result.produce_price_id == price.produce_price_id
    assert result.cooperative_id == price.cooperative_id
    assert result.price_per_unit == price.price_per_unit


def test_get_missing_produce_price_returns_404(db_session):
    service = ProducePriceService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        service.get_produce_price(uuid4())

    assert exc_info.value.status_code == 404


def test_list_produce_prices(db_session, produce_graph):
    service = ProducePriceService(db_session)
    price = produce_graph.price

    results = service.list_produce_prices(
        cooperative_id=price.cooperative_id,
    )

    assert any(item.produce_price_id == price.produce_price_id for item in results)


def test_count_produce_prices(db_session, produce_graph):
    service = ProducePriceService(db_session)
    price = produce_graph.price

    result = service.count_produce_prices(
        cooperative_id=price.cooperative_id,
    )

    assert result >= 1


def test_create_produce_price(db_session, produce_graph):
    service = ProducePriceService(db_session)
    cooperative = produce_graph.cooperative
    agent = produce_graph.agent

    effective_from = datetime(2035, 1, 1, tzinfo=timezone.utc)

    payload = ProducePriceCreate(
        cooperative_id=cooperative.cooperative_id,
        unit="lb",
        price_per_unit=Decimal("400.00"),
        effective_from=effective_from,
        effective_to=None,
        created_by_user_id=agent.user_id,
    )
    result = service.create_produce_price(payload)

    assert result.produce_price_id is not None
    assert result.cooperative_id == cooperative.cooperative_id
    assert result.unit == "lb"
    assert result.price_per_unit == Decimal("400.00")
    assert result.created_by_user_id == agent.user_id


def test_update_produce_price(db_session, produce_graph):
    service = ProducePriceService(db_session)
    price = produce_graph.price

    payload = ProducePriceUpdate(
        price_per_unit=Decimal("375.00"),
    )

    result = service.update_produce_price(
        price.produce_price_id,
        payload,
    )

    assert result.price_per_unit == Decimal("375.00")


def test_update_missing_produce_price_returns_404(db_session):
    service = ProducePriceService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        service.update_produce_price(
            uuid4(),
            ProducePriceUpdate(price_per_unit=Decimal("375.00")),
        )

    assert exc_info.value.status_code == 404


def test_create_price_with_invalid_period_returns_400(
    db_session,
    produce_graph,
):
    service = ProducePriceService(db_session)
    cooperative = produce_graph.cooperative
    agent = produce_graph.agent

    effective_from = datetime(2035, 1, 2, tzinfo=timezone.utc)
    effective_to = effective_from - timedelta(days=1)

    payload = ProducePriceCreate(
        cooperative_id=cooperative.cooperative_id,
        unit="lb",
        price_per_unit=Decimal("400.00"),
        effective_from=effective_from,
        effective_to=effective_to,
        created_by_user_id=agent.user_id,
    )

    with pytest.raises(HTTPException) as exc_info:
        service.create_produce_price(payload)

    assert exc_info.value.status_code == 400


def test_create_price_with_overlapping_period_returns_409(
    db_session,
    produce_graph,
):
    service = ProducePriceService(db_session)
    price = produce_graph.price
    agent = produce_graph.agent

    payload = ProducePriceCreate(
        cooperative_id=price.cooperative_id,
        unit=price.unit,
        price_per_unit=Decimal("400.00"),
        effective_from=price.effective_from + timedelta(minutes=1),
        effective_to=None,
        created_by_user_id=agent.user_id,
    )

    with pytest.raises(HTTPException) as exc_info:
        service.create_produce_price(payload)

    assert exc_info.value.status_code == 409


def test_deactivate_produce_price(db_session, produce_graph):
    service = ProducePriceService(db_session)
    price = produce_graph.price

    # Use a price whose effective period has already started.
    price.effective_from = datetime(2020, 1, 1, tzinfo=timezone.utc)
    db_session.commit()
    db_session.refresh(price)

    result = service.deactivate_produce_price(
        price.produce_price_id,
    )

    assert result.effective_to is not None


def test_deactivate_missing_produce_price_returns_404(db_session):
    service = ProducePriceService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        service.deactivate_produce_price(uuid4())

    assert exc_info.value.status_code == 404


def test_delete_produce_price(db_session, produce_graph):
    service = ProducePriceService(db_session)
    price = produce_graph.price
    price_id = price.produce_price_id

    service.delete_produce_price(price_id)

    assert service.repository.get_by_id(price_id) is None


def test_delete_missing_produce_price_returns_404(db_session):
    service = ProducePriceService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        service.delete_produce_price(uuid4())

    assert exc_info.value.status_code == 404
