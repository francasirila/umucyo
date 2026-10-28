from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from conftest import make_produce_record, produce_record_payload
from models.enums import AccountStatus
from repositories.produce_record import ProduceRecordRepository
from schemas.produce_record import (
    ProduceRecordCreate,
    ProduceRecordResponse,
    ProduceRecordUpdate,
)
from services.produce_record import ProduceRecordService


@pytest.fixture()
def service(db_session):
    return ProduceRecordService(db_session)


BASE_PAYLOAD = {
    "cooperative_id": uuid4(),
    "produce_price_id": uuid4(),
    "farmer_id": uuid4(),
    "device_id": uuid4(),
    "collection_point_id": uuid4(),
    "delivery_status": "accepted",
    "user_id": uuid4(),
    "gross_weight_kg": "75.500",
    "agent_notes": "Clean coffee cherries",
}


def test_create_schema_accepts_valid_payload():
    record = ProduceRecordCreate(**BASE_PAYLOAD)
    assert record.gross_weight_kg == Decimal("75.500")
    assert record.agent_notes == "Clean coffee cherries"


def test_create_schema_converts_numeric_strings_to_decimal():
    record = ProduceRecordCreate(**BASE_PAYLOAD)
    assert isinstance(record.gross_weight_kg, Decimal)


def test_create_schema_rejects_zero_or_negative_weight():
    with pytest.raises(ValidationError):
        ProduceRecordCreate(**{**BASE_PAYLOAD, "gross_weight_kg": "0"})
    with pytest.raises(ValidationError):
        ProduceRecordCreate(**{**BASE_PAYLOAD, "gross_weight_kg": "-1.5"})


def test_create_schema_does_not_accept_an_amount():
    # The amount is calculated by the backend from the produce price.
    assert "amount" not in ProduceRecordCreate.model_fields
    assert "amount" not in ProduceRecordUpdate.model_fields


def test_create_schema_rejects_values_exceeding_column_precision():
    # Numeric(10, 3) allows 7 integer digits.
    with pytest.raises(ValidationError):
        ProduceRecordCreate(**{**BASE_PAYLOAD, "gross_weight_kg": "12345678.000"})


def test_create_schema_rejects_unknown_delivery_status():
    with pytest.raises(ValidationError):
        ProduceRecordCreate(**{**BASE_PAYLOAD, "delivery_status": "pending"})


def test_create_schema_allows_missing_notes():
    payload = {key: value for key, value in BASE_PAYLOAD.items() if key != "agent_notes"}
    assert ProduceRecordCreate(**payload).agent_notes is None


def test_update_schema_is_fully_optional_and_excludes_foreign_keys():
    assert ProduceRecordUpdate().model_dump(exclude_unset=True) == {}
    assert set(ProduceRecordUpdate.model_fields.keys()) == {
        "delivery_status",
        "gross_weight_kg",
        "agent_notes",
    }


def test_response_schema_reads_from_model_attributes():
    class FakeRecord:
        produce_record_id = uuid4()
        cooperative_id = uuid4()
        produce_price_id = uuid4()
        farmer_id = uuid4()
        device_id = uuid4()
        collection_point_id = uuid4()
        delivery_status = "rejected"
        user_id = uuid4()
        gross_weight_kg = Decimal("50.000")
        agent_notes = None
        amount = Decimal("10000.00")
        recorded_at = "2026-10-28T10:00:00+00:00"

    response = ProduceRecordResponse.model_validate(FakeRecord())
    assert response.delivery_status == "rejected"
    assert response.recorded_at is not None


def test_repository_creates_and_fetches_record(db_session, produce_graph):
    repository = ProduceRecordRepository(db_session)
    created = make_produce_record(produce_graph)

    fetched = repository.get_by_id(created.produce_record_id)
    assert fetched is not None
    assert fetched.gross_weight_kg == Decimal("75.5")
    assert fetched.amount == Decimal("26425.00")


def test_repository_get_by_id_returns_none_for_missing(db_session):
    assert ProduceRecordRepository(db_session).get_by_id(uuid4()) is None


def test_repository_list_orders_newest_first(db_session, produce_graph):
    repository = ProduceRecordRepository(db_session)
    older = make_produce_record(produce_graph, recorded_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    newer = make_produce_record(produce_graph, recorded_at=datetime(2026, 6, 1, tzinfo=timezone.utc))

    records = repository.list()
    assert [r.produce_record_id for r in records] == [
        newer.produce_record_id,
        older.produce_record_id,
    ]


def test_repository_list_filters_by_status_farmer_and_point(db_session, produce_graph):
    from conftest import build_graph

    repository = ProduceRecordRepository(db_session)
    record = make_produce_record(produce_graph)

    other_graph = build_graph(db_session)
    make_produce_record(other_graph, delivery_status="rejected", amount=0)

    assert [r.produce_record_id for r in repository.list(delivery_status="accepted")] == [record.produce_record_id]
    assert [r.produce_record_id for r in repository.list(farmer_id=record.farmer_id)] == [record.produce_record_id]
    assert [r.produce_record_id for r in repository.list(collection_point_id=record.collection_point_id)] == [
        record.produce_record_id
    ]


def test_repository_list_filters_by_date_range(db_session, produce_graph):
    repository = ProduceRecordRepository(db_session)
    june = make_produce_record(produce_graph, recorded_at=datetime(2026, 6, 1, tzinfo=timezone.utc))
    make_produce_record(produce_graph, recorded_at=datetime(2026, 1, 1, tzinfo=timezone.utc))

    records = repository.list(recorded_from=datetime(2026, 3, 1, tzinfo=timezone.utc))
    assert [r.produce_record_id for r in records] == [june.produce_record_id]


def test_repository_list_paginates(db_session, produce_graph):
    repository = ProduceRecordRepository(db_session)
    for index in range(5):
        make_produce_record(produce_graph, recorded_at=datetime(2026, 1, index + 1, tzinfo=timezone.utc))

    assert len(repository.list(skip=2, limit=2)) == 2
    assert repository.count() == 5
    assert repository.count(delivery_status="accepted") == 5


def test_repository_update_applies_only_given_fields(db_session, produce_graph):
    repository = ProduceRecordRepository(db_session)
    record = make_produce_record(produce_graph)

    updated = repository.update(record, {"agent_notes": "Updated notes"})

    assert updated.agent_notes == "Updated notes"
    assert updated.gross_weight_kg == Decimal("75.5")
    assert updated.delivery_status == "accepted"


def test_repository_delete_removes_record(db_session, produce_graph):
    repository = ProduceRecordRepository(db_session)
    record = make_produce_record(produce_graph)

    repository.delete(record)

    assert repository.get_by_id(record.produce_record_id) is None


def test_service_create_persists_valid_record(service, produce_graph):
    record = service.create_produce_record(ProduceRecordCreate(**produce_record_payload(produce_graph)))

    assert record.produce_record_id is not None
    assert record.farmer_id == produce_graph.farmer.user_id
    assert record.recorded_at is not None
    # 75.5 kg x 350.00 per kg, calculated by the backend.
    assert record.amount == Decimal("26425.00")


@pytest.mark.parametrize(
    "field",
    ["cooperative_id", "produce_price_id", "farmer_id", "device_id", "collection_point_id", "user_id"],
)
def test_service_create_returns_404_for_unknown_reference(service, produce_graph, field):
    payload = produce_record_payload(produce_graph, **{field: "00000000-0000-0000-0000-000000000042"})

    with pytest.raises(HTTPException) as exc_info:
        service.create_produce_record(ProduceRecordCreate(**payload))
    assert exc_info.value.status_code == 404


def test_service_create_rejects_price_from_another_cooperative(service, produce_graph, db_session):
    from conftest import _make_cooperative, _make_price

    other_coop = _make_cooperative(db_session, cooperative_name="Other Coop", email="other@test.rw")
    foreign_price = _make_price(db_session, other_coop, produce_graph.agent)
    payload = produce_record_payload(produce_graph, produce_price_id=str(foreign_price.produce_price_id))

    with pytest.raises(HTTPException) as exc_info:
        service.create_produce_record(ProduceRecordCreate(**payload))
    assert exc_info.value.status_code == 422
    assert "cooperative" in exc_info.value.detail


def test_service_create_rejects_device_from_another_collection_point(service, produce_graph, db_session):
    from conftest import _make_collection_point, _make_device

    other_point = _make_collection_point(db_session, produce_graph.cooperative, collection_name="Far Away")
    stray_device = _make_device(db_session, other_point)
    payload = produce_record_payload(produce_graph, device_id=str(stray_device.device_id))

    with pytest.raises(HTTPException) as exc_info:
        service.create_produce_record(ProduceRecordCreate(**payload))
    assert exc_info.value.status_code == 422
    assert "collection point" in exc_info.value.detail


def test_service_create_rejects_farmer_from_another_collection_point(service, produce_graph, db_session):
    from conftest import _make_collection_point, _make_farmer

    other_point = _make_collection_point(db_session, produce_graph.cooperative, collection_name="Other Point")
    stranger = _make_farmer(db_session, other_point, produce_graph.agent)
    payload = produce_record_payload(produce_graph, farmer_id=str(stranger.user_id))

    with pytest.raises(HTTPException) as exc_info:
        service.create_produce_record(ProduceRecordCreate(**payload))
    assert exc_info.value.status_code == 422
    assert "collection point" in exc_info.value.detail


def test_service_create_rejects_inactive_device(service, produce_graph, db_session):
    from conftest import _make_device

    broken = _make_device(db_session, produce_graph.collection_point, status=AccountStatus.inactive)
    payload = produce_record_payload(produce_graph, device_id=str(broken.device_id))

    with pytest.raises(HTTPException) as exc_info:
        service.create_produce_record(ProduceRecordCreate(**payload))
    assert exc_info.value.status_code == 422
    assert "not active" in exc_info.value.detail


def test_service_create_rejects_inactive_collection_point(service, produce_graph, db_session):
    from conftest import _make_collection_point, _make_device, _make_farmer

    closed_point = _make_collection_point(db_session, produce_graph.cooperative, status=AccountStatus.inactive)
    closed_device = _make_device(db_session, closed_point)
    closed_farmer = _make_farmer(db_session, closed_point, produce_graph.agent)
    payload = produce_record_payload(
        produce_graph,
        collection_point_id=str(closed_point.collection_point_id),
        device_id=str(closed_device.device_id),
        farmer_id=str(closed_farmer.user_id),
    )

    with pytest.raises(HTTPException) as exc_info:
        service.create_produce_record(ProduceRecordCreate(**payload))
    assert exc_info.value.status_code == 422
    assert "not active" in exc_info.value.detail


def test_service_create_rejected_delivery_has_zero_amount(service, produce_graph):
    payload = produce_record_payload(produce_graph, delivery_status="rejected")

    record = service.create_produce_record(ProduceRecordCreate(**payload))
    assert record.delivery_status == "rejected"
    assert record.amount == 0


def test_service_get_raises_404_for_missing_record(service):
    with pytest.raises(HTTPException) as exc_info:
        service.get_produce_record(uuid4())
    assert exc_info.value.status_code == 404


def test_service_update_changes_only_provided_fields(service, produce_graph):
    record = make_produce_record(produce_graph)

    updated = service.update_produce_record(record.produce_record_id, ProduceRecordUpdate(agent_notes="Moisture slightly high"))

    assert updated.agent_notes == "Moisture slightly high"
    assert updated.gross_weight_kg == record.gross_weight_kg
    assert updated.delivery_status == "accepted"


def test_service_update_to_rejected_recalculates_amount_to_zero(service, produce_graph):
    record = make_produce_record(produce_graph)

    updated = service.update_produce_record(record.produce_record_id, ProduceRecordUpdate(delivery_status="rejected"))

    assert updated.delivery_status == "rejected"
    assert updated.amount == 0


def test_service_update_weight_recalculates_amount(service, produce_graph):
    record = make_produce_record(produce_graph)

    updated = service.update_produce_record(record.produce_record_id, ProduceRecordUpdate(gross_weight_kg=10))

    assert updated.gross_weight_kg == 10
    assert updated.amount == Decimal("3500.00")  # 10 kg x 350.00


def test_service_delete_removes_record(service, produce_graph):
    record = make_produce_record(produce_graph)

    service.delete_produce_record(record.produce_record_id)

    with pytest.raises(HTTPException) as exc_info:
        service.get_produce_record(record.produce_record_id)
    assert exc_info.value.status_code == 404


def test_api_post_creates_produce_record(api_client, produce_graph):
    response = api_client.post("/produce-records", json=produce_record_payload(produce_graph))

    assert response.status_code == 201
    body = response.json()
    assert body["produce_record_id"]
    assert body["delivery_status"] == "accepted"
    assert body["farmer_id"] == str(produce_graph.farmer.user_id)
    assert body["recorded_at"]
    # Amount is calculated by the backend: 75.5 kg x 350.00.
    assert float(body["amount"]) == 26425.00


def test_api_post_returns_422_for_invalid_weight(api_client, produce_graph):
    response = api_client.post("/produce-records", json=produce_record_payload(produce_graph, gross_weight_kg="0"))
    assert response.status_code == 422


def test_api_post_returns_404_for_unknown_farmer(api_client, produce_graph):
    response = api_client.post(
        "/produce-records",
        json=produce_record_payload(produce_graph, farmer_id="00000000-0000-0000-0000-000000000042"),
    )
    assert response.status_code == 404


def test_api_post_rejected_delivery_returns_zero_amount(api_client, produce_graph):
    response = api_client.post("/produce-records", json=produce_record_payload(produce_graph, delivery_status="rejected"))

    assert response.status_code == 201
    assert float(response.json()["amount"]) == 0


def test_api_get_by_id_returns_record(api_client, produce_graph):
    record = make_produce_record(produce_graph)

    response = api_client.get(f"/produce-records/{record.produce_record_id}")

    assert response.status_code == 200
    assert response.json()["produce_record_id"] == str(record.produce_record_id)


def test_api_get_by_id_returns_404_for_missing_record(api_client):
    assert api_client.get(f"/produce-records/{uuid4()}").status_code == 404


def test_api_list_returns_all_records(api_client, produce_graph):
    make_produce_record(produce_graph)
    make_produce_record(produce_graph, delivery_status="rejected", amount=0)

    response = api_client.get("/produce-records")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_api_list_filters_and_paginates(api_client, produce_graph):
    kept = make_produce_record(produce_graph)
    make_produce_record(produce_graph, delivery_status="rejected", amount=0)

    filtered = api_client.get("/produce-records", params={"delivery_status": "accepted"}).json()
    assert [r["produce_record_id"] for r in filtered] == [str(kept.produce_record_id)]

    paged = api_client.get("/produce-records", params={"skip": 0, "limit": 1}).json()
    assert len(paged) == 1


def test_api_patch_updates_only_provided_fields(api_client, produce_graph):
    record = make_produce_record(produce_graph)

    response = api_client.patch(f"/produce-records/{record.produce_record_id}", json={"agent_notes": "Reviewed"})

    assert response.status_code == 200
    body = response.json()
    assert body["agent_notes"] == "Reviewed"
    assert body["delivery_status"] == "accepted"


def test_api_patch_returns_404_for_missing_record(api_client):
    assert api_client.patch(f"/produce-records/{uuid4()}", json={"agent_notes": "x"}).status_code == 404


def test_api_patch_to_rejected_sets_amount_to_zero(api_client, produce_graph):
    make_produce_record(produce_graph)
    record = api_client.get("/produce-records").json()[0]

    response = api_client.patch(f"/produce-records/{record['produce_record_id']}", json={"delivery_status": "rejected"})

    assert response.status_code == 200
    assert float(response.json()["amount"]) == 0


def test_api_delete_returns_204_and_removes_record(api_client, produce_graph):
    record = make_produce_record(produce_graph)

    assert api_client.delete(f"/produce-records/{record.produce_record_id}").status_code == 204
    assert api_client.get(f"/produce-records/{record.produce_record_id}").status_code == 404


def test_api_delete_returns_404_for_missing_record(api_client):
    assert api_client.delete(f"/produce-records/{uuid4()}").status_code == 404
