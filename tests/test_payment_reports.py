"""Payment reports for the cooperative dashboard: list, detail and status update."""

import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from database import get_db
from main import app
from models.payment_report import PaymentReport
from services.payment_report import PaymentReportService
from tests.support import FARMER_PHONE, make_session_factory, seed_world

URL = "/api/v1/payment-reports"


@pytest.fixture()
def db():
    factory, engine = make_session_factory()
    session = factory()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture()
def world(db):
    return seed_world(db)


@pytest.fixture()
def client(db):
    def override():
        yield db

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def add_report(db, cooperative_id, farmer_id, **overrides):
    data = {
        "payment_report_id": uuid.uuid4(),
        "cooperative_id": cooperative_id,
        "farmer_id": farmer_id,
        "report_type": "less_payment",
        "reported_month_start": date(2026, 9, 1),
        "reported_month_label": "Sep 2026",
        "description": "Farmer reports less payment for Sep 2026",
        "status": "pending",
        "confirmation_sms_sent": True,
        "created_at": datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc),
    }
    data.update(overrides)
    report = PaymentReport(**data)
    db.add(report)
    db.commit()
    return report


def mine(db, world, **overrides):
    return add_report(db, world.mine.coop, world.mine.farmer, **overrides)


def ids(response):
    return [row["payment_report_id"] for row in response.json()]


# ---------- list ----------
def test_list_is_newest_first(client, db, world):
    old = mine(db, world, created_at=datetime(2026, 10, 1, tzinfo=timezone.utc))
    new = mine(db, world, created_at=datetime(2026, 10, 3, tzinfo=timezone.utc))
    response = client.get(URL, params={"cooperative_id": str(world.mine.coop)})
    assert response.status_code == 200
    assert ids(response) == [str(new.payment_report_id), str(old.payment_report_id)]


def test_list_has_everything_the_dashboard_needs(client, db, world):
    mine(db, world)
    row = client.get(URL, params={"cooperative_id": str(world.mine.coop)}).json()[0]
    assert set(row) == {
        "payment_report_id",
        "farmer_id",
        "farmer_name",
        "farmer_phone",
        "report_type",
        "reported_month_start",
        "reported_month_label",
        "description",
        "status",
        "confirmation_sms_sent",
        "created_at",
    }
    assert row["farmer_name"] == "John Doe"
    assert row["farmer_phone"] == FARMER_PHONE
    assert row["report_type"] == "less_payment"
    assert row["reported_month_label"] == "Sep 2026"
    assert row["status"] == "pending"
    assert row["confirmation_sms_sent"] is True


def test_other_cooperatives_reports_never_appear(client, db, world):
    mine(db, world)
    add_report(db, world.other.coop, world.other.farmer)
    response = client.get(URL, params={"cooperative_id": str(world.mine.coop)})
    assert len(response.json()) == 1
    assert response.json()[0]["farmer_name"] == "John Doe"


def test_no_reports_gives_an_empty_list(client, world):
    response = client.get(URL, params={"cooperative_id": str(world.mine.coop)})
    assert response.status_code == 200 and response.json() == []


def test_unknown_cooperative_gives_an_empty_list(client, db, world):
    mine(db, world)
    response = client.get(URL, params={"cooperative_id": str(uuid.uuid4())})
    assert response.status_code == 200 and response.json() == []


@pytest.mark.parametrize("status", ["pending", "resolved", "rejected"])
def test_filter_by_status(client, db, world, status):
    for state in ("pending", "resolved", "rejected"):
        mine(db, world, status=state)
    response = client.get(URL, params={"cooperative_id": str(world.mine.coop), "status": status})
    assert [row["status"] for row in response.json()] == [status]


def test_an_unknown_status_filter_is_refused(client, world):
    response = client.get(URL, params={"cooperative_id": str(world.mine.coop), "status": "done"})
    assert response.status_code == 422


def test_pagination(client, db, world):
    created = [
        mine(db, world, created_at=datetime(2026, 10, day, tzinfo=timezone.utc))
        for day in range(1, 6)
    ]
    newest_first = [str(r.payment_report_id) for r in reversed(created)]
    base = {"cooperative_id": str(world.mine.coop)}
    first = client.get(URL, params={**base, "limit": 2, "offset": 0})
    second = client.get(URL, params={**base, "limit": 2, "offset": 2})
    assert ids(first) == newest_first[:2]
    assert ids(second) == newest_first[2:4]


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 201}, {"offset": -1}, {"limit": "x"}])
def test_bad_paging_is_refused(client, world, params):
    response = client.get(URL, params={"cooperative_id": str(world.mine.coop), **params})
    assert response.status_code == 422


@pytest.mark.parametrize("params", [{}, {"cooperative_id": "not-a-uuid"}])
def test_cooperative_id_is_required_and_must_be_a_uuid(client, params):
    assert client.get(URL, params=params).status_code == 422


# ---------- detail ----------
def test_detail(client, db, world):
    report = mine(db, world)
    response = client.get(
        f"{URL}/{report.payment_report_id}", params={"cooperative_id": str(world.mine.coop)}
    )
    assert response.status_code == 200
    assert response.json()["payment_report_id"] == str(report.payment_report_id)


def test_detail_unknown_report(client, world):
    response = client.get(f"{URL}/{uuid.uuid4()}", params={"cooperative_id": str(world.mine.coop)})
    assert response.status_code == 404


def test_detail_of_another_cooperatives_report_is_not_found(client, db, world):
    report = mine(db, world)
    response = client.get(
        f"{URL}/{report.payment_report_id}", params={"cooperative_id": str(world.other.coop)}
    )
    assert response.status_code == 404


def test_detail_needs_a_cooperative_id(client, db, world):
    report = mine(db, world)
    assert client.get(f"{URL}/{report.payment_report_id}").status_code == 422


# ---------- status update ----------
def patch(client, report_id, coop, body):
    return client.patch(
        f"{URL}/{report_id}/status", params={"cooperative_id": str(coop)}, json=body
    )


@pytest.mark.parametrize("status", ["resolved", "rejected", "pending"])
def test_the_status_can_be_changed(client, db, world, status):
    report = mine(db, world, status="rejected" if status == "pending" else "pending")
    response = patch(client, report.payment_report_id, world.mine.coop, {"status": status})
    assert response.status_code == 200 and response.json()["status"] == status
    db.refresh(report)
    assert report.status == status


def test_a_resolved_report_leaves_the_pending_list(client, db, world):
    report = mine(db, world)
    patch(client, report.payment_report_id, world.mine.coop, {"status": "resolved"})
    pending = client.get(URL, params={"cooperative_id": str(world.mine.coop), "status": "pending"})
    assert pending.json() == []


def test_an_invalid_status_is_refused_and_nothing_changes(client, db, world):
    report = mine(db, world)
    response = patch(client, report.payment_report_id, world.mine.coop, {"status": "done"})
    assert response.status_code == 422
    db.refresh(report)
    assert report.status == "pending"


def test_the_body_is_required(client, db, world):
    report = mine(db, world)
    response = client.patch(
        f"{URL}/{report.payment_report_id}/status", params={"cooperative_id": str(world.mine.coop)}
    )
    assert response.status_code == 422


def test_unknown_report_cannot_be_updated(client, world):
    response = patch(client, uuid.uuid4(), world.mine.coop, {"status": "resolved"})
    assert response.status_code == 404


def test_another_cooperative_cannot_change_a_report(client, db, world):
    report = mine(db, world)
    response = patch(client, report.payment_report_id, world.other.coop, {"status": "resolved"})
    assert response.status_code == 404
    db.refresh(report)
    assert report.status == "pending"


# ---------- service without a database ----------
class FakeReports:
    def __init__(self, report=None):
        self.report, self.updated = report, []

    def get(self, payment_report_id, cooperative_id):
        return self.report

    def update_status(self, report, status):
        self.updated.append(status)
        report.status = status
        return report


def fake_report(**overrides):
    data = {
        "payment_report_id": uuid.uuid4(),
        "farmer_id": uuid.uuid4(),
        "farmer": SimpleNamespace(first_name="John", last_name="Doe", phone_number="0788123456"),
        "report_type": "not_paid",
        "reported_month_start": date(2026, 9, 1),
        "reported_month_label": "Sep 2026",
        "description": "x",
        "status": "pending",
        "confirmation_sms_sent": False,
        "created_at": datetime(2026, 10, 1, tzinfo=timezone.utc),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def test_service_turns_a_report_into_the_dashboard_shape():
    out = PaymentReportService(None, reports=FakeReports()).to_output(fake_report())
    assert out.farmer_name == "John Doe" and out.farmer_phone == "0788123456"
    assert out.report_type == "not_paid" and out.confirmation_sms_sent is False


def test_service_returns_none_for_a_missing_report_and_updates_nothing():
    fake = FakeReports(report=None)
    service = PaymentReportService(None, reports=fake)
    assert service.get_report(uuid.uuid4(), uuid.uuid4()) is None
    assert service.update_status(uuid.uuid4(), uuid.uuid4(), "resolved") is None
    assert fake.updated == []


def test_service_updates_through_the_repository():
    fake = FakeReports(report=fake_report())
    result = PaymentReportService(None, reports=fake).update_status(
        uuid.uuid4(), uuid.uuid4(), "resolved"
    )
    assert fake.updated == ["resolved"] and result.status == "resolved"
