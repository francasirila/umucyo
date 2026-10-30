import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Enum as SAEnum, select

from database import get_db
from main import app
from models import CollectionPoint, Cooperative, ProduceRecord, WeighingDevice
from models.enums import AccountStatus, CooperativeStatus
from repositories.weighing_device import WeighingDeviceRepository
from schemas.weighing_device import WeighingDeviceCreate, WeighingDeviceUpdate
from services.weighing_device import WeighingDeviceService


def test_weighing_device_table_name():
    assert WeighingDevice.__tablename__ == "weighing_device"


def test_weighing_device_has_expected_columns():
    expected = ["device_id", "collection_point_id", "serial_number", "status", "registered_at"]
    assert expected == [column.name for column in WeighingDevice.__table__.columns if column.name in expected]
    assert set(expected).issubset(set(WeighingDevice.__table__.columns.keys()))


def test_weighing_device_has_primary_key():
    assert WeighingDevice.__table__.primary_key.columns


def test_weighing_device_serial_number_max_length_is_100():
    assert WeighingDevice.__table__.columns["serial_number"].type.length == 100


def test_weighing_device_status_column_uses_account_status_enum_with_active_default():
    column = WeighingDevice.__table__.columns["status"]
    assert isinstance(column.type, SAEnum)
    assert column.type.enum_class is AccountStatus
    assert column.default.arg == AccountStatus.active


def test_weighing_device_collection_point_foreign_key():
    foreign_keys = list(WeighingDevice.__table__.columns["collection_point_id"].foreign_keys)
    assert len(foreign_keys) == 1
    assert foreign_keys[0].target_fullname == "collection_point.collection_point_id"


def test_weighing_device_relationships_defined():
    relationships = {rel.key: rel.mapper.class_ for rel in WeighingDevice.__mapper__.relationships}
    assert relationships["collection_point"] is CollectionPoint
    assert relationships["produce_records"] is ProduceRecord


def test_weighing_device_model_round_trip(db_session, collection_point):
    device = WeighingDevice(
        collection_point_id=collection_point.collection_point_id,
        serial_number="WD-MODEL-1",
    )
    db_session.add(device)
    db_session.commit()

    fetched = db_session.scalar(select(WeighingDevice).where(WeighingDevice.serial_number == "WD-MODEL-1"))
    assert fetched is not None
    assert fetched.status == AccountStatus.active
    assert fetched.registered_at is not None


@pytest.fixture()
def cooperative(db_session):
    coop = Cooperative(
        cooperative_name="Umucyo Cooperative",
        location="Huye District",
        email="info@umucyo-test.rw",
        status=CooperativeStatus.active,
    )
    db_session.add(coop)
    db_session.commit()
    return coop


@pytest.fixture()
def collection_point(db_session, cooperative):
    point = CollectionPoint(
        cooperative_id=cooperative.cooperative_id,
        collection_name="Kimironko Collection Point",
        status=AccountStatus.active,
    )
    db_session.add(point)
    db_session.commit()
    return point


@pytest.fixture()
def repository(db_session):
    return WeighingDeviceRepository(db_session)


@pytest.fixture()
def service(db_session):
    return WeighingDeviceService(db_session)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def make_device(collection_point, serial_number="WD-TEST-0001", status=AccountStatus.active):
    return WeighingDevice(
        collection_point_id=collection_point.collection_point_id,
        serial_number=serial_number,
        status=status,
    )


def payload(collection_point_id, serial_number="WD-TEST-0001", status="active"):
    return {
        "collection_point_id": str(collection_point_id),
        "serial_number": serial_number,
        "status": status,
    }


def test_repository_create_persists_device(repository, collection_point):
    device = repository.create(make_device(collection_point))

    assert device.device_id is not None
    assert device.registered_at is not None
    stored = repository.get_by_id(device.device_id)
    assert stored is not None
    assert stored.serial_number == "WD-TEST-0001"
    assert stored.collection_point_id == collection_point.collection_point_id


def test_repository_get_by_id_returns_none_for_missing(repository):
    assert repository.get_by_id(uuid.uuid4()) is None


def test_repository_get_by_serial_number(repository, collection_point):
    device = repository.create(make_device(collection_point, serial_number="WD-UNIQUE-01"))

    found = repository.get_by_serial_number("WD-UNIQUE-01")
    assert found is not None
    assert found.device_id == device.device_id
    assert repository.get_by_serial_number("WD-DOES-NOT-EXIST") is None


def test_repository_get_all_filters_by_collection_point(repository, collection_point, cooperative, db_session):
    other_point = CollectionPoint(
        cooperative_id=cooperative.cooperative_id,
        collection_name="Other Collection Point",
        status=AccountStatus.active,
    )
    db_session.add(other_point)
    db_session.commit()

    repository.create(make_device(collection_point, "WD-A"))
    repository.create(make_device(other_point, "WD-B"))

    devices = repository.get_all(collection_point_id=collection_point.collection_point_id)
    assert [d.serial_number for d in devices] == ["WD-A"]


def test_repository_get_all_filters_by_status(repository, collection_point):
    repository.create(make_device(collection_point, "WD-ACTIVE", AccountStatus.active))
    repository.create(make_device(collection_point, "WD-INACTIVE", AccountStatus.inactive))

    active = repository.get_all(status=AccountStatus.active)
    inactive = repository.get_all(status=AccountStatus.inactive)

    assert [d.serial_number for d in active] == ["WD-ACTIVE"]
    assert [d.serial_number for d in inactive] == ["WD-INACTIVE"]


def test_repository_get_all_paginates(repository, collection_point):
    for index in range(5):
        repository.create(make_device(collection_point, f"WD-PAGE-{index}"))

    page_one = repository.get_all(limit=2)
    page_two = repository.get_all(limit=2, skip=2)

    assert len(page_one) == 2
    assert len(page_two) == 2
    all_serials = {d.serial_number for d in repository.get_all(limit=10)}
    assert {d.serial_number for d in page_one + page_two}.issubset(all_serials)
    assert repository.count() == 5


def test_repository_update_persists_changes(repository, collection_point):
    device = repository.create(make_device(collection_point))
    device.status = AccountStatus.inactive

    updated = repository.update(device)

    assert updated.status == AccountStatus.inactive
    assert repository.get_by_id(device.device_id).status == AccountStatus.inactive


def test_repository_delete_removes_device(repository, collection_point):
    device = repository.create(make_device(collection_point))

    repository.delete(device)

    assert repository.get_by_id(device.device_id) is None


def test_service_create_device_success(service, collection_point):
    device = service.create_device(
        WeighingDeviceCreate(
            collection_point_id=collection_point.collection_point_id,
            serial_number="WD-SVC-0001",
        )
    )

    assert device.serial_number == "WD-SVC-0001"
    assert device.status == AccountStatus.active


def test_service_create_device_unknown_collection_point_raises_404(service):
    with pytest.raises(Exception) as exc_info:
        service.create_device(WeighingDeviceCreate(collection_point_id=uuid.uuid4(), serial_number="WD-SVC-404"))
    assert getattr(exc_info.value, "status_code", None) == 404


def test_service_create_device_duplicate_serial_raises_409(service, collection_point):
    service.create_device(WeighingDeviceCreate(collection_point_id=collection_point.collection_point_id, serial_number="WD-DUP"))

    with pytest.raises(Exception) as exc_info:
        service.create_device(
            WeighingDeviceCreate(collection_point_id=collection_point.collection_point_id, serial_number="WD-DUP")
        )
    assert getattr(exc_info.value, "status_code", None) == 409


def test_service_get_device_returns_device(service, collection_point):
    created = service.create_device(
        WeighingDeviceCreate(collection_point_id=collection_point.collection_point_id, serial_number="WD-GET")
    )

    assert service.get_device(created.device_id).serial_number == "WD-GET"


def test_service_get_device_missing_raises_404(service):
    with pytest.raises(Exception) as exc_info:
        service.get_device(uuid.uuid4())
    assert getattr(exc_info.value, "status_code", None) == 404


def test_service_update_device_changes_serial_and_status(service, collection_point):
    device = service.create_device(
        WeighingDeviceCreate(collection_point_id=collection_point.collection_point_id, serial_number="WD-OLD")
    )

    updated = service.update_device(device.device_id, WeighingDeviceUpdate(serial_number="WD-NEW", status=AccountStatus.inactive))

    assert updated.serial_number == "WD-NEW"
    assert updated.status == AccountStatus.inactive


def test_service_update_device_to_taken_serial_raises_409(service, collection_point):
    service.create_device(
        WeighingDeviceCreate(collection_point_id=collection_point.collection_point_id, serial_number="WD-TAKEN")
    )
    device = service.create_device(
        WeighingDeviceCreate(collection_point_id=collection_point.collection_point_id, serial_number="WD-FREE")
    )

    with pytest.raises(Exception) as exc_info:
        service.update_device(device.device_id, WeighingDeviceUpdate(serial_number="WD-TAKEN"))
    assert getattr(exc_info.value, "status_code", None) == 409


def test_service_update_device_keeping_own_serial_does_not_conflict(service, collection_point):
    device = service.create_device(
        WeighingDeviceCreate(collection_point_id=collection_point.collection_point_id, serial_number="WD-KEEP")
    )

    updated = service.update_device(device.device_id, WeighingDeviceUpdate(serial_number="WD-KEEP"))

    assert updated.serial_number == "WD-KEEP"


def test_service_update_device_partial_payload_only_changes_status(service, collection_point):
    device = service.create_device(
        WeighingDeviceCreate(collection_point_id=collection_point.collection_point_id, serial_number="WD-PART")
    )

    updated = service.update_device(device.device_id, WeighingDeviceUpdate(status=AccountStatus.inactive))

    assert updated.serial_number == "WD-PART"
    assert updated.status == AccountStatus.inactive


def test_service_delete_device_removes_it(service, collection_point):
    device = service.create_device(
        WeighingDeviceCreate(collection_point_id=collection_point.collection_point_id, serial_number="WD-DEL")
    )

    service.delete_device(device.device_id)

    with pytest.raises(Exception) as exc_info:
        service.get_device(device.device_id)
    assert getattr(exc_info.value, "status_code", None) == 404


def test_service_list_devices_applies_filters(service, collection_point):
    service.create_device(WeighingDeviceCreate(collection_point_id=collection_point.collection_point_id, serial_number="WD-L1"))
    service.create_device(
        WeighingDeviceCreate(
            collection_point_id=collection_point.collection_point_id,
            serial_number="WD-L2",
            status=AccountStatus.inactive,
        )
    )

    assert len(service.list_devices()) == 2
    assert [d.serial_number for d in service.list_devices(device_status=AccountStatus.inactive)] == ["WD-L2"]


def test_api_post_creates_device_with_201(client, collection_point):
    response = client.post("/weighing-devices", json=payload(collection_point.collection_point_id))

    assert response.status_code == 201
    body = response.json()
    assert body["serial_number"] == "WD-TEST-0001"
    assert body["status"] == "active"
    assert body["collection_point_id"] == str(collection_point.collection_point_id)
    assert body["registered_at"] is not None


def test_api_post_rejects_invalid_payload_with_422(client, collection_point):
    response = client.post("/weighing-devices", json=payload(collection_point.collection_point_id, "X" * 101))

    assert response.status_code == 422


def test_api_post_unknown_collection_point_returns_404(client):
    response = client.post("/weighing-devices", json=payload(uuid.uuid4()))

    assert response.status_code == 404
    assert response.json()["detail"] == "Collection point not found"


def test_api_post_duplicate_serial_returns_409(client, collection_point):
    client.post("/weighing-devices", json=payload(collection_point.collection_point_id, "WD-API-DUP"))

    response = client.post("/weighing-devices", json=payload(collection_point.collection_point_id, "WD-API-DUP"))

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_api_get_lists_all_devices(client, collection_point):
    client.post("/weighing-devices", json=payload(collection_point.collection_point_id, "WD-API-1"))
    client.post("/weighing-devices", json=payload(collection_point.collection_point_id, "WD-API-2"))

    response = client.get("/weighing-devices")

    assert response.status_code == 200
    serials = {d["serial_number"] for d in response.json()}
    assert {"WD-API-1", "WD-API-2"}.issubset(serials)


def test_api_get_filters_by_collection_point_and_status(client, collection_point, cooperative, db_session):
    other_point = CollectionPoint(
        cooperative_id=cooperative.cooperative_id,
        collection_name="API Other Point",
        status=AccountStatus.active,
    )
    db_session.add(other_point)
    db_session.commit()
    client.post("/weighing-devices", json=payload(collection_point.collection_point_id, "WD-FILT-1"))
    client.post("/weighing-devices", json=payload(other_point.collection_point_id, "WD-FILT-2"))

    response = client.get(
        "/weighing-devices",
        params={"collection_point_id": str(collection_point.collection_point_id), "status": "active"},
    )

    assert response.status_code == 200
    assert [d["serial_number"] for d in response.json()] == ["WD-FILT-1"]


def test_api_get_device_by_id(client, collection_point):
    created = client.post("/weighing-devices", json=payload(collection_point.collection_point_id, "WD-API-GET")).json()

    response = client.get(f"/weighing-devices/{created['device_id']}")

    assert response.status_code == 200
    assert response.json()["serial_number"] == "WD-API-GET"


def test_api_get_unknown_device_returns_404(client):
    response = client.get(f"/weighing-devices/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Weighing device not found"


def test_api_patch_updates_device(client, collection_point):
    created = client.post("/weighing-devices", json=payload(collection_point.collection_point_id, "WD-API-PATCH")).json()

    response = client.patch(
        f"/weighing-devices/{created['device_id']}",
        json={"serial_number": "WD-API-PATCHED", "status": "inactive"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["serial_number"] == "WD-API-PATCHED"
    assert body["status"] == "inactive"


def test_api_delete_returns_204_and_device_is_gone(client, collection_point):
    created = client.post("/weighing-devices", json=payload(collection_point.collection_point_id, "WD-API-DEL")).json()

    response = client.delete(f"/weighing-devices/{created['device_id']}")

    assert response.status_code == 204
    assert client.get(f"/weighing-devices/{created['device_id']}").status_code == 404


def test_repository_get_all_empty_returns_empty_list(repository):
    assert repository.get_all() == []


def test_repository_count_empty_is_zero(repository):
    assert repository.count() == 0


def test_repository_get_all_orders_newest_first(repository, collection_point):
    now = datetime.now(timezone.utc)

    older = make_device(collection_point, "WD-OLD")
    older.registered_at = now - timedelta(hours=2)
    middle = make_device(collection_point, "WD-MID")
    middle.registered_at = now - timedelta(hours=1)
    newest = make_device(collection_point, "WD-NEW")
    newest.registered_at = now

    for device in (older, middle, newest):
        repository.create(device)

    devices = repository.get_all()
    assert [d.serial_number for d in devices] == ["WD-NEW", "WD-MID", "WD-OLD"]


def test_repository_get_all_skip_beyond_total_returns_empty(repository, collection_point):
    repository.create(make_device(collection_point))

    assert repository.get_all(skip=10) == []


def test_service_create_device_honours_inactive_status(service, collection_point):
    device = service.create_device(
        WeighingDeviceCreate(
            collection_point_id=collection_point.collection_point_id,
            serial_number="WD-OFF",
            status=AccountStatus.inactive,
        )
    )

    assert device.status == AccountStatus.inactive


def test_service_update_device_missing_raises_404(service):
    with pytest.raises(Exception) as exc_info:
        service.update_device(uuid.uuid4(), WeighingDeviceUpdate(status=AccountStatus.active))
    assert getattr(exc_info.value, "status_code", None) == 404


def test_service_delete_device_missing_raises_404(service):
    with pytest.raises(Exception) as exc_info:
        service.delete_device(uuid.uuid4())
    assert getattr(exc_info.value, "status_code", None) == 404


def test_service_list_devices_paginates(service, collection_point):
    for index in range(4):
        service.create_device(
            WeighingDeviceCreate(collection_point_id=collection_point.collection_point_id, serial_number=f"WD-P{index}")
        )

    page = service.list_devices(skip=1, limit=2)

    assert len(page) == 2
    all_serials = {d.serial_number for d in service.list_devices()}
    assert {d.serial_number for d in page}.issubset(all_serials)


def test_service_list_devices_filters_by_collection_point(service, collection_point, cooperative, db_session):
    other_point = CollectionPoint(
        cooperative_id=cooperative.cooperative_id,
        collection_name="Service Other Point",
        status=AccountStatus.active,
    )
    db_session.add(other_point)
    db_session.commit()
    service.create_device(WeighingDeviceCreate(collection_point_id=collection_point.collection_point_id, serial_number="WD-C1"))
    service.create_device(WeighingDeviceCreate(collection_point_id=other_point.collection_point_id, serial_number="WD-C2"))

    result = service.list_devices(collection_point_id=other_point.collection_point_id)
    assert [d.serial_number for d in result] == ["WD-C2"]


def test_api_post_missing_serial_returns_422(client, collection_point):
    body = payload(collection_point.collection_point_id)
    body.pop("serial_number")

    response = client.post("/weighing-devices", json=body)

    assert response.status_code == 422


def test_api_post_missing_collection_point_returns_422(client):
    body = payload(uuid.uuid4())
    body.pop("collection_point_id")

    response = client.post("/weighing-devices", json=body)

    assert response.status_code == 422


def test_api_post_accepts_inactive_status(client, collection_point):
    response = client.post("/weighing-devices", json=payload(collection_point.collection_point_id, "WD-INACT", "inactive"))

    assert response.status_code == 201
    assert response.json()["status"] == "inactive"


def test_api_get_invalid_uuid_returns_422(client):
    response = client.get("/weighing-devices/not-a-uuid")

    assert response.status_code == 422


def test_api_patch_unknown_device_returns_404(client):
    response = client.patch(f"/weighing-devices/{uuid.uuid4()}", json={"status": "inactive"})

    assert response.status_code == 404


def test_api_delete_unknown_device_returns_404(client):
    response = client.delete(f"/weighing-devices/{uuid.uuid4()}")

    assert response.status_code == 404


def test_api_patch_empty_payload_makes_no_changes(client, collection_point):
    created = client.post("/weighing-devices", json=payload(collection_point.collection_point_id, "WD-SAME")).json()

    response = client.patch(f"/weighing-devices/{created['device_id']}", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["serial_number"] == "WD-SAME"
    assert body["status"] == "active"


def test_api_list_rejects_invalid_limit_with_422(client):
    assert client.get("/weighing-devices", params={"limit": 0}).status_code == 422
    assert client.get("/weighing-devices", params={"limit": 101}).status_code == 422
    assert client.get("/weighing-devices", params={"skip": -1}).status_code == 422


def test_api_list_respects_limit(client, collection_point):
    for index in range(3):
        client.post("/weighing-devices", json=payload(collection_point.collection_point_id, f"WD-LIM-{index}"))

    response = client.get("/weighing-devices", params={"limit": 2})

    assert response.status_code == 200
    assert len(response.json()) == 2
