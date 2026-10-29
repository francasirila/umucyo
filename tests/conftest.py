import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-long-enough-for-hmac"
os.environ["BOOTSTRAP_SECRET"] = ""

import uuid
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import database
import main
from core.rate_limit import limiter
from database import Base
from models.collection_point import CollectionPoint
from models.cooperative import Cooperative
from models.cooperative_user import CooperativeAdmin, CooperativeAgent
from models.enums import AccountStatus, UserRole
from models.farmer import Farmer
from services import agent_service, auth_service, farmer_service

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
    monkeypatch.setattr(agent_service, "send_invitation_email", box.send_invitation)
    monkeypatch.setattr(farmer_service, "send_sms", box.send_sms)
    return box


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
    return payload


@pytest.fixture()
def auth_headers(cooperative_admin, login):
    return login(cooperative_admin["email"], cooperative_admin["password"])


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
