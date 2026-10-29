import pytest

from core.exceptions import ServiceError
from models.audit_log import AuditLog
from models.enums import AccountStatus
from schemas.collection_point import CollectionPointCreate, CollectionPointUpdate
from services.collection_point import CollectionPointService


def audit_count(db, action):
    return db.query(AuditLog).filter_by(action=action).count()


def test_create_trims_name_and_writes_audit(db_session, seeded):
    point = CollectionPointService(db_session).create(seeded.admin, CollectionPointCreate(collection_name="  New Point "))
    assert point.collection_name == "New Point"
    assert point.status == AccountStatus.active
    assert audit_count(db_session, "create_collection_point") == 1


def test_create_duplicate_raises_409(db_session, seeded):
    with pytest.raises(ServiceError) as exc:
        CollectionPointService(db_session).create(seeded.admin, CollectionPointCreate(collection_name="seed point"))
    assert exc.value.status_code == 409


def test_create_rejects_blank_name(db_session, seeded):
    with pytest.raises(ServiceError) as exc:
        CollectionPointService(db_session).create(seeded.admin, CollectionPointCreate(collection_name="   "))
    assert exc.value.status_code == 422


def test_agent_cannot_create(db_session, seeded):
    with pytest.raises(ServiceError) as exc:
        CollectionPointService(db_session).create(seeded.agent, CollectionPointCreate(collection_name="Agent Point"))
    assert exc.value.status_code == 403


def test_agent_list_returns_only_assigned_point(db_session, seeded):
    service = CollectionPointService(db_session)
    service.create(seeded.admin, CollectionPointCreate(collection_name="Another"))

    names = [p.collection_name for p in service.list_points(seeded.agent)]
    assert names == ["Seed Point"]


def test_agent_without_point_sees_nothing(db_session, seeded):
    seeded.agent.collection_point_id = None
    db_session.commit()
    assert CollectionPointService(db_session).list_points(seeded.agent) == []


def test_agent_cannot_get_other_point(db_session, seeded):
    service = CollectionPointService(db_session)
    other = service.create(seeded.admin, CollectionPointCreate(collection_name="Another"))

    with pytest.raises(ServiceError) as exc:
        service.get_point(seeded.agent, other.collection_point_id)
    assert exc.value.status_code == 404


def test_update_without_changes_raises_422(db_session, seeded):
    with pytest.raises(ServiceError) as exc:
        CollectionPointService(db_session).update(seeded.admin, seeded.point.collection_point_id, CollectionPointUpdate())
    assert exc.value.status_code == 422


def test_update_records_audit_with_old_and_new_values(db_session, seeded):
    CollectionPointService(db_session).update(
        seeded.admin,
        seeded.point.collection_point_id,
        CollectionPointUpdate(collection_name="Renamed Point"),
    )
    entry = db_session.query(AuditLog).filter_by(action="update_collection_point").one()
    assert entry.old_values == {"collection_name": "Seed Point"}
    assert entry.new_values == {"collection_name": "Renamed Point"}


def test_deactivate_is_idempotent_and_audited_once(db_session, seeded):
    service = CollectionPointService(db_session)
    service.deactivate(seeded.admin, seeded.point.collection_point_id)
    point = service.deactivate(seeded.admin, seeded.point.collection_point_id)

    assert point.status == AccountStatus.inactive
    assert audit_count(db_session, "deactivate_collection_point") == 1
