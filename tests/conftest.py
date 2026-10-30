import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-long-enough-for-hmac"
os.environ["BOOTSTRAP_SECRET"] = ""

import uuid
from types import SimpleNamespace

import pytest
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from routers.produce_record import router

import database
import main
from core.rate_limit import limiter
from database import Base
from models.collection_point import CollectionPoint
from models.cooperative import Cooperative
from models.cooperative_user import CooperativeAdmin, CooperativeAgent
from models.enums import AccountStatus, UserRole
from models.farmer import Farmer
from services import auth_service
from services import user_service

ADMIN_EMAIL = "admin@sulwe.com"
ADMIN_PASSWORD = "SecurePassword123"
AGENT_PASSWORD = "AgentPassword123"


class Outbox:
    def __init__(self):
        self.otps, self.invitations, self.sms = [], [], []
        self.fail_otp = False
        self.fail_invitation = False
        self.sms_result = True

    @property
    def last_otp(self):
        return self.otps[-1]["code"]

    def send_otp(self, email, otp):
        if self.fail_otp:
            raise RuntimeError("SMTP down")
        self.otps.append({"email": email, "code": otp})

    def send_invitation(self, email, first_name, link, purpose="invitation"):
        if self.fail_invitation:
            raise RuntimeError("SMTP down")
        self.invitations.append({"email": email, "first_name": first_name, "link": link, "purpose": purpose})
        return True

    def send_sms(self, phone_number, message):
        self.sms.append({"phone_number": phone_number, "message": message})
        return self.sms_result


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture(autouse=True)
def outbox(monkeypatch):
    box = Outbox()
    monkeypatch.setattr(auth_service, "send_login_otp", box.send_otp)
    monkeypatch.setattr(user_service, "send_invitation_email", box.send_invitation)
    monkeypatch.setattr(user_service, "send_sms", box.send_sms)
    return box
from database import Base, get_db
from models import (
    CollectionPoint,
    Cooperative,
    CooperativeUser,
    Farmer,
    ProducePrice,
    ProduceRecord,
    WeighingDevice,
)


@pytest.fixture()
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    database.engine = engine
    database.SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def db_session(engine):
    session = database.SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(engine):
    def override_get_db():
        db = database.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[database.get_db] = override_get_db
    with TestClient(main.app) as test_client:
        yield test_client
    main.app.dependency_overrides.clear()


@pytest.fixture()
def login(client, outbox):
    def _login(email, password):
        response = client.post("/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200, response.text
        verification = client.post("/auth/verify-otp", json={"email": email, "code": outbox.last_otp})
        assert verification.status_code == 200, verification.text
        return {"Authorization": f"Bearer {verification.json()['access_token']}"}

    return _login


@pytest.fixture()
def cooperative_admin(client):
    payload = {
        "cooperative_name": "Auth Cooperative",
        "email": ADMIN_EMAIL,
        "first_name": "Admin",
        "last_name": "User",
        "password": ADMIN_PASSWORD,
    }
    response = client.post("/auth/register/cooperative", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["admin"]
    cooperative = Cooperative(
        **{
            "cooperative_name": "Umucyo Test Cooperative",
            "location": "Huye, Rwanda",
            "email": "coop@test.rw",
            **overrides,
        }
    )
    db_session.add(cooperative)
    db_session.commit()
    db_session.refresh(cooperative)
    return cooperative


def _make_collection_point(db_session, cooperative, **overrides) -> CollectionPoint:
    collection_point = CollectionPoint(
        **{
            "cooperative_id": cooperative.cooperative_id,
            "collection_name": "Main Collection Point",
            **overrides,
        }
    )
    db_session.add(collection_point)
    db_session.commit()
    db_session.refresh(collection_point)
    return collection_point


def _make_agent(db_session, cooperative, **overrides) -> CooperativeUser:
    agent = CooperativeUser(
        **{
            "first_name": "Alice",
            "last_name": "Uwase",
            "password_hash": "test-hash",
            "email": "alice@test.rw",
            "cooperative_id": cooperative.cooperative_id,
            **overrides,
        }
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    return agent


def _make_farmer(db_session, collection_point, registered_by, **overrides) -> Farmer:
    farmer = Farmer(
        **{
            "farmer_id": uuid.uuid4(),
            "first_name": "Jean",
            "last_name": "Nkusi",
            "collection_point_id": collection_point.collection_point_id,
            "registered_by_user_id": registered_by.user_id,
            "phone_number": "+250788000002",
            **overrides,
        }
    )
    db_session.add(farmer)
    db_session.commit()
    db_session.refresh(farmer)
    return farmer


def _make_device(db_session, collection_point, **overrides) -> WeighingDevice:
    device = WeighingDevice(
        **{
            "collection_point_id": collection_point.collection_point_id,
            "serial_number": "UMC-DEV-TEST",
            **overrides,
        }
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


def _make_price(db_session, cooperative, created_by, **overrides) -> ProducePrice:
    price = ProducePrice(
        **{
            "cooperative_id": cooperative.cooperative_id,
            "unit": "kg",
            "price_per_unit": 350,
            "effective_from": datetime.now(timezone.utc),
            "created_by_user_id": created_by.user_id,
            **overrides,
        }
    )
    db_session.add(price)
    db_session.commit()
    db_session.refresh(price)
    return price


def build_graph(db_session) -> SimpleNamespace:
    cooperative = _make_cooperative(db_session)
    collection_point = _make_collection_point(db_session, cooperative)
    agent = _make_agent(db_session, cooperative)
    farmer = _make_farmer(db_session, collection_point, agent)
    device = _make_device(db_session, collection_point)
    price = _make_price(db_session, cooperative, agent)
    return SimpleNamespace(
        db=db_session,
        cooperative=cooperative,
        collection_point=collection_point,
        agent=agent,
        farmer=farmer,
        device=device,
        price=price,
    )


@pytest.fixture()
def produce_graph(db_session) -> SimpleNamespace:
    return build_graph(db_session)


def make_produce_record(graph: SimpleNamespace, **overrides) -> ProduceRecord:
    record = ProduceRecord(
        **{
            "cooperative_id": graph.cooperative.cooperative_id,
            "produce_price_id": graph.price.produce_price_id,
            "farmer_id": graph.farmer.user_id,
            "device_id": graph.device.device_id,
            "collection_point_id": graph.collection_point.collection_point_id,
            "delivery_status": "accepted",
            "user_id": graph.agent.user_id,
            "gross_weight_kg": 75.5,
            "agent_notes": "Clean coffee cherries",
            "amount": 26425.00,
            **overrides,
        }
    )
    graph.db.add(record)
    graph.db.commit()
    graph.db.refresh(record)
    return record


def produce_record_payload(graph: SimpleNamespace, **overrides) -> dict:
    payload = {
        "cooperative_id": str(graph.cooperative.cooperative_id),
        "produce_price_id": str(graph.price.produce_price_id),
        "farmer_id": str(graph.farmer.user_id),
        "device_id": str(graph.device.device_id),
        "collection_point_id": str(graph.collection_point.collection_point_id),
        "delivery_status": "accepted",
        "user_id": str(graph.agent.user_id),
        "gross_weight_kg": "75.500",
        "agent_notes": "Clean coffee cherries",
        **overrides,
    }
    return payload


@pytest.fixture()
def auth_headers(cooperative_admin, login):
    return login(ADMIN_EMAIL, ADMIN_PASSWORD)


@pytest.fixture()
def other_auth_headers(client, login):
    payload = {
        "cooperative_name": "Other Cooperative",
        "location": "Huye",
        "email": "other-admin@example.com",
        "first_name": "Other",
        "last_name": "Admin",
        "password": ADMIN_PASSWORD,
    }
    assert client.post("/auth/register/cooperative", json=payload).status_code == 201
    return login(payload["email"], payload["password"])


@pytest.fixture()
def make_point(client):
    def _make(headers, name="Main Collection"):
        response = client.post(
            "/collection-points/",
            headers=headers,
            json={"collection_name": name},
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture()
def make_agent(client, outbox, login):
    def _make(headers, point_id, email="agent@example.com", activate=True):
        response = client.post(
            "/users/agents",
            headers=headers,
            json={
                "first_name": "Agent",
                "last_name": "One",
                "email": email,
                "collection_point_id": point_id,
            },
        )
        assert response.status_code == 201, response.text
        agent = response.json()["agent"]

        if not activate:
            return {"agent": agent, "headers": None}

        token = outbox.invitations[-1]["link"].split("token=", 1)[1]
        password = client.post("/auth/set-password", json={"token": token, "password": AGENT_PASSWORD})
        assert password.status_code == 200, password.text

        return {"agent": agent, "headers": login(email, AGENT_PASSWORD), "token": token}

    return _make


@pytest.fixture()
def seeded(db_session):
    """One cooperative, point, admin, agent and farmer inserted directly."""
    coop = Cooperative(cooperative_name="Seed Coop", email="seed-coop@example.com")
    db_session.add(coop)
    db_session.flush()

    point = CollectionPoint(
        cooperative_id=coop.cooperative_id,
        collection_name="Seed Point",
        status=AccountStatus.active,
    )
    db_session.add(point)
    db_session.flush()

    admin = CooperativeAdmin(
        first_name="Seed",
        last_name="Admin",
        user_type=UserRole.admin,
        status=AccountStatus.active,
        email="seed-admin@example.com",
        password_hash="x",
        cooperative_id=coop.cooperative_id,
    )
    agent = CooperativeAgent(
        first_name="Seed",
        last_name="Agent",
        user_type=UserRole.agent,
        status=AccountStatus.active,
        email="seed-agent@example.com",
        password_hash="x",
        cooperative_id=coop.cooperative_id,
        collection_point_id=point.collection_point_id,
    )
    db_session.add_all([admin, agent])
    db_session.flush()

    farmer = Farmer(
        farmer_id=uuid.uuid4(),
        first_name="Seed",
        last_name="Farmer",
        user_type=UserRole.farmer,
        status=AccountStatus.active,
        phone_number="+250788000001",
        collection_point_id=point.collection_point_id,
        registered_by_user_id=admin.user_id,
    )
    db_session.add(farmer)
    db_session.commit()

    return SimpleNamespace(cooperative=coop, point=point, admin=admin, agent=agent, farmer=farmer)
def api_client(db_session):

    app = FastAPI()
    app.include_router(router)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
