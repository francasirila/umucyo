from core.config import settings


def test_duplicate_cooperative_email_rejected(client):
    payload = {
        "cooperative_name": "First Cooperative",
        "email": "same@example.com",
        "first_name": "First",
        "last_name": "Admin",
        "password": "SecurePassword123",
    }

    first = client.post("/auth/register/cooperative", json=payload)
    assert first.status_code == 201, first.text

    payload["cooperative_name"] = "Second Cooperative"

    second = client.post("/auth/register/cooperative", json=payload)
    assert second.status_code == 409, second.text


def test_invalid_login_rejected(client, cooperative_admin):
    response = client.post(
        "/auth/login",
        json={
            "email": "admin@sulwe.com",
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 401


def test_invalid_otp_rejected(client, cooperative_admin):
    response = client.post(
        "/auth/verify-otp",
        json={
            "email": "admin@sulwe.com",
            "code": "000000",
        },
    )

    assert response.status_code == 401


def test_bootstrap_key_required_and_bootstrap_is_single_use(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "BOOTSTRAP_SECRET",
        "bootstrap-secret-for-tests",
    )

    payload = {
        "cooperative_name": "Bootstrapped Cooperative",
        "email": "seed@example.com",
        "first_name": "Seed",
        "last_name": "Admin",
        "password": "SecurePassword123",
    }

    missing_key = client.post(
        "/auth/bootstrap-admin",
        json=payload,
    )

    assert missing_key.status_code == 403

    created = client.post(
        "/auth/bootstrap-admin",
        json=payload,
        headers={"X-Bootstrap-Key": "bootstrap-secret-for-tests"},
    )

    assert created.status_code == 201, created.text

    payload["email"] = "second-seed@example.com"
    payload["cooperative_name"] = "Another Cooperative"

    second_attempt = client.post(
        "/auth/bootstrap-admin",
        json=payload,
        headers={"X-Bootstrap-Key": "bootstrap-secret-for-tests"},
    )

    assert second_attempt.status_code == 409


def test_me_requires_authentication(client, auth_headers):
    unauthenticated = client.get("/auth/me")
    assert unauthenticated.status_code == 401

    authenticated = client.get(
        "/auth/me",
        headers=auth_headers,
    )

    assert authenticated.status_code == 200


def test_logout_requires_authentication(client, auth_headers):
    assert client.post("/auth/logout").status_code == 401

    response = client.post(
        "/auth/logout",
        headers=auth_headers,
    )

    assert response.status_code == 200


def test_logout_does_not_revoke_stateless_token(client, auth_headers):
    logout = client.post(
        "/auth/logout",
        headers=auth_headers,
    )

    assert logout.status_code == 200

    me = client.get("/auth/me", headers=auth_headers)
    assert me.status_code == 200


def test_set_password_rejects_unknown_invitation(client):
    response = client.post(
        "/auth/set-password",
        json={
            "token": "x" * 30,
            "password": "SecurePassword123",
        },
    )

    assert response.status_code == 400


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
