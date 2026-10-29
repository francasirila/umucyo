from datetime import datetime, timedelta, timezone

from models.enums import AccountStatus, UserRole
from repositories.audit_repository import AuditRepository
from repositories.collection_point import CollectionPointRepository
from repositories.otp_repository import OTPRepository
from repositories.user_repository import UserRepository


def test_point_repo_get_by_name_is_case_insensitive(db_session, seeded):
    repo = CollectionPointRepository(db_session)
    found = repo.get_by_name(seeded.cooperative.cooperative_id, "  SEED point ")
    assert found.collection_point_id == seeded.point.collection_point_id


def test_point_repo_create_update_delete(db_session, seeded):
    repo = CollectionPointRepository(db_session)
    point = repo.create(
        {
            "cooperative_id": seeded.cooperative.cooperative_id,
            "collection_name": "Repo Point",
            "status": AccountStatus.active,
        }
    )
    assert repo.get_by_id(point.collection_point_id) is point

    repo.update(point, {"collection_name": "Renamed"})
    assert point.collection_name == "Renamed"

    repo.delete(point)
    assert repo.get_by_id(point.collection_point_id) is None


def test_point_repo_list_filters_by_status(db_session, seeded):
    repo = CollectionPointRepository(db_session)
    inactive = repo.create(
        {
            "cooperative_id": seeded.cooperative.cooperative_id,
            "collection_name": "Aaa Inactive",
            "status": AccountStatus.inactive,
        }
    )
    coop_id = seeded.cooperative.cooperative_id

    assert [p.collection_name for p in repo.list_by_cooperative(coop_id)] == ["Aaa Inactive", "Seed Point"]
    assert repo.list_by_cooperative(coop_id, AccountStatus.inactive) == [inactive]


def test_user_repo_lookups(db_session, seeded):
    repo = UserRepository(db_session)

    assert repo.get_by_email(" SEED-ADMIN@example.com ").user_id == seeded.admin.user_id
    assert repo.get_by_email("nobody@example.com") is None
    assert repo.get_by_phone_number("+250788000001").user_id == seeded.farmer.user_id
    assert repo.get_by_id(seeded.admin.user_id).user_id == seeded.admin.user_id


def test_user_repo_active_farmer_by_phone(db_session, seeded):
    repo = UserRepository(db_session)
    assert repo.get_active_farmer_by_phone_number("+250788000001") is not None

    seeded.farmer.status = AccountStatus.inactive
    db_session.commit()
    assert repo.get_active_farmer_by_phone_number("+250788000001") is None


def test_user_repo_create_picks_model_from_role(db_session, seeded):
    repo = UserRepository(db_session)
    created = repo.create(
        {
            "first_name": "New",
            "last_name": "Admin",
            "role": UserRole.admin,
            "email": "repo-created@example.com",
            "password_hash": "x",
            "cooperative_id": seeded.cooperative.cooperative_id,
        }
    )
    assert created.role == UserRole.admin
    assert type(created).__name__ == "CooperativeAdmin"


def test_user_repo_list_for_cooperative_filters_by_role(db_session, seeded):
    repo = UserRepository(db_session)
    coop_id = seeded.cooperative.cooperative_id

    assert len(repo.list_for_cooperative(coop_id)) == 3
    assert [u.user_id for u in repo.list_for_cooperative(coop_id, role=UserRole.farmer)] == [seeded.farmer.user_id]
    assert repo.list_for_cooperative(coop_id, skip=0, limit=1).__len__() == 1


def test_user_repo_list_farmers_at_points(db_session, seeded):
    repo = UserRepository(db_session)
    point_id = seeded.point.collection_point_id

    assert repo.list_farmers_at_points([]) == []
    assert [f.user_id for f in repo.list_farmers_at_points([point_id])] == [seeded.farmer.user_id]
    future = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1)
    assert repo.list_farmers_at_points([point_id], since=future) == []


def test_otp_repo_active_latest_and_consume(db_session, seeded):
    repo = OTPRepository(db_session)
    user_id = seeded.admin.user_id

    repo.create(
        {
            "user_id": user_id,
            "otp_hash": "h",
            "attempts": 0,
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
        }
    )
    db_session.commit()

    assert repo.get_active(user_id) is not None
    assert repo.get_latest(user_id) is not None

    repo.consume_active(user_id, datetime.now(timezone.utc))
    db_session.commit()

    assert repo.get_active(user_id) is None
    assert repo.get_latest(user_id) is not None


def test_audit_repo_create_and_list(db_session, seeded):
    repo = AuditRepository(db_session)
    coop_id = seeded.cooperative.cooperative_id

    for action, entity in [("a1", "user"), ("a2", "collection_point")]:
        repo.create(
            {
                "user_id": seeded.admin.user_id,
                "action": action,
                "entity_type": entity,
                "entity_id": seeded.point.collection_point_id,
            }
        )
    db_session.commit()

    assert len(repo.list_for_cooperative(coop_id)) == 2
    only_users = repo.list_for_cooperative(coop_id, entity_type="user")
    assert [a.action for a in only_users] == ["a1"]
    assert len(repo.list_for_cooperative(coop_id, limit=1)) == 1
