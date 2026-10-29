from datetime import datetime, timedelta, timezone

from sqlalchemy import update

from core.config import settings
from models.agent_invitation import AgentInvitation
from models.login_otp import LoginOTP

ADMIN = {"email": "admin@sulwe.com", "password": "SecurePassword123"}


def test_cooperative_registration_and_login(client, outbox):
    payload = {
        "cooperative_name": "Umucyo Tea",
        "email": "owner@example.com",
        "first_name": "Aline",
        "last_name": "Uwase",
        "password": "SecurePassword123",
    }

    registration = client.post("/auth/register/cooperative", json=payload)
    assert registration.status_code == 201, registration.text
    assert registration.json()["admin"]["role"] == "admin"
    assert "password" not in registration.text

    login = client.post("/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert login.status_code == 200, login.text
    assert login.json()["requires_otp"] is True
    assert len(outbox.otps) == 1

    verification = client.post("/auth/verify-otp", json={"email": payload["email"], "code": outbox.last_otp})
    assert verification.status_code == 200, verification.text
    assert verification.json()["token_type"] == "bearer"
    assert verification.json()["user"]["email"] == payload["email"]


def test_email_is_case_insensitive_on_login(client, cooperative_admin):
    response = client.post("/auth/login", json={"email": "ADMIN@Sulwe.com", "password": ADMIN["password"]})
    assert response.status_code == 200, response.text


def test_duplicate_cooperative_email_rejected(client):
    payload = {
        "cooperative_name": "First Cooperative",
        "email": "same@example.com",
        "first_name": "First",
        "last_name": "Admin",
        "password": "SecurePassword123",
    }
    assert client.post("/auth/register/cooperative", json=payload).status_code == 201

    payload["cooperative_name"] = "Second Cooperative"
    assert client.post("/auth/register/cooperative", json=payload).status_code == 409


def test_duplicate_cooperative_name_rejected(client):
    payload = {
        "cooperative_name": "Same Name",
        "email": "one@example.com",
        "first_name": "A",
        "last_name": "B",
        "password": "SecurePassword123",
    }
    assert client.post("/auth/register/cooperative", json=payload).status_code == 201

    payload["email"] = "two@example.com"
    assert client.post("/auth/register/cooperative", json=payload).status_code == 409


def test_registration_validates_required_fields(client):
    response = client.post(
        "/auth/register/cooperative",
        json={
            "cooperative_name": "A",
            "email": "not-an-email",
            "first_name": "",
            "last_name": "Admin",
            "password": "short",
        },
    )
    assert response.status_code == 422


def test_invalid_login_rejected(client, cooperative_admin):
    response = client.post("/auth/login", json={"email": ADMIN["email"], "password": "WrongPassword123"})
    assert response.status_code == 401


def test_unknown_account_login_rejected(client):
    response = client.post("/auth/login", json={"email": "ghost@example.com", "password": "Whatever123"})
    assert response.status_code == 401


def test_login_fails_with_503_when_email_cannot_be_sent(client, cooperative_admin, outbox):
    outbox.fail_otp = True
    response = client.post("/auth/login", json=ADMIN)
    assert response.status_code == 503


def test_login_is_rate_limited(client, cooperative_admin):
    bad = {"email": ADMIN["email"], "password": "WrongPassword123"}
    statuses = [client.post("/auth/login", json=bad).status_code for _ in range(6)]
    assert statuses[:5] == [401] * 5
    assert statuses[5] == 429


def test_invalid_otp_rejected_when_none_requested(client, cooperative_admin):
    response = client.post("/auth/verify-otp", json={"email": ADMIN["email"], "code": "000000"})
    assert response.status_code == 401


def test_otp_must_be_six_digits(client, cooperative_admin):
    response = client.post("/auth/verify-otp", json={"email": ADMIN["email"], "code": "12ab56"})
    assert response.status_code == 422


def test_wrong_otp_rejected_then_locked_after_five_attempts(client, cooperative_admin, outbox):
    client.post("/auth/login", json=ADMIN)

    for _ in range(5):
        wrong = client.post("/auth/verify-otp", json={"email": ADMIN["email"], "code": "000000"})
        assert wrong.status_code == 401

    locked = client.post("/auth/verify-otp", json={"email": ADMIN["email"], "code": outbox.last_otp})
    assert locked.status_code == 429


def test_otp_cannot_be_reused(client, cooperative_admin, outbox):
    client.post("/auth/login", json=ADMIN)
    body = {"email": ADMIN["email"], "code": outbox.last_otp}

    assert client.post("/auth/verify-otp", json=body).status_code == 200
    assert client.post("/auth/verify-otp", json=body).status_code == 401


def test_expired_otp_rejected(client, cooperative_admin, outbox, db_session):
    client.post("/auth/login", json=ADMIN)

    db_session.execute(update(LoginOTP).values(expires_at=datetime.now(timezone.utc) - timedelta(minutes=1)))
    db_session.commit()

    response = client.post("/auth/verify-otp", json={"email": ADMIN["email"], "code": outbox.last_otp})
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


def test_resend_otp_replaces_previous_code(client, cooperative_admin, outbox):
    client.post("/auth/login", json=ADMIN)

    resend = client.post("/auth/resend-otp", json={"email": ADMIN["email"]})
    assert resend.status_code == 200, resend.text
    assert len(outbox.otps) == 2

    verification = client.post("/auth/verify-otp", json={"email": ADMIN["email"], "code": outbox.last_otp})
    assert verification.status_code == 200, verification.text


def test_resend_otp_for_unknown_account(client):
    response = client.post("/auth/resend-otp", json={"email": "ghost@example.com"})
    assert response.status_code == 404


def test_bootstrap_key_required_and_bootstrap_is_single_use(client, monkeypatch):
    monkeypatch.setattr(settings, "BOOTSTRAP_SECRET", "bootstrap-secret-for-tests")

    payload = {
        "cooperative_name": "Bootstrapped Cooperative",
        "email": "seed@example.com",
        "first_name": "Seed",
        "last_name": "Admin",
        "password": "SecurePassword123",
    }

    assert client.post("/auth/bootstrap-admin", json=payload).status_code == 403
    assert client.post("/auth/bootstrap-admin", json=payload, headers={"X-Bootstrap-Key": "wrong"}).status_code == 403

    key = {"X-Bootstrap-Key": "bootstrap-secret-for-tests"}
    assert client.post("/auth/bootstrap-admin", json=payload, headers=key).status_code == 201

    payload["email"] = "second-seed@example.com"
    payload["cooperative_name"] = "Another Cooperative"
    assert client.post("/auth/bootstrap-admin", json=payload, headers=key).status_code == 409


def test_bootstrap_disabled_when_no_secret_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "BOOTSTRAP_SECRET", "")
    payload = {
        "cooperative_name": "X Coop",
        "email": "x@example.com",
        "first_name": "X",
        "last_name": "Y",
        "password": "SecurePassword123",
    }
    response = client.post("/auth/bootstrap-admin", json=payload, headers={"X-Bootstrap-Key": ""})
    assert response.status_code == 403


def test_me_requires_authentication(client, auth_headers):
    assert client.get("/auth/me").status_code == 401

    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == ADMIN["email"]
    assert response.json()["role"] == "admin"


def test_logout_requires_authentication(client, auth_headers):
    assert client.post("/auth/logout").status_code == 401
    assert client.post("/auth/logout", headers=auth_headers).status_code == 200


def test_logout_does_not_revoke_stateless_token(client, auth_headers):
    assert client.post("/auth/logout", headers=auth_headers).status_code == 200
    assert client.get("/auth/me", headers=auth_headers).status_code == 200


def test_set_password_rejects_unknown_invitation(client):
    response = client.post("/auth/set-password", json={"token": "x" * 30, "password": "SecurePassword123"})
    assert response.status_code == 400


def test_set_password_rejects_short_password(client):
    response = client.post("/auth/set-password", json={"token": "x" * 30, "password": "short"})
    assert response.status_code == 422


def test_set_password_rejects_expired_invitation(client, auth_headers, make_point, make_agent, outbox, db_session):
    point = make_point(auth_headers)
    make_agent(auth_headers, point["collection_point_id"], activate=False)
    token = outbox.invitations[-1]["link"].split("token=", 1)[1]

    db_session.execute(update(AgentInvitation).values(expires_at=datetime.now(timezone.utc) - timedelta(hours=1)))
    db_session.commit()

    response = client.post("/auth/set-password", json={"token": token, "password": "AgentPassword123"})
    assert response.status_code == 400


def test_invitation_cannot_be_used_twice(client, auth_headers, make_point, make_agent):
    point = make_point(auth_headers)
    agent = make_agent(auth_headers, point["collection_point_id"])

    again = client.post("/auth/set-password", json={"token": agent["token"], "password": "AnotherPass123"})
    assert again.status_code == 400
