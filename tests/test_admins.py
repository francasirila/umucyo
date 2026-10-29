def admin_payload(**overrides):
    payload = {
        "first_name": "New",
        "last_name": "Admin",
        "email": "new-admin@example.com",
        "password": "SecurePassword123",
    }
    payload.update(overrides)
    return payload


def test_admin_can_create_another_admin(client, auth_headers, login):
    response = client.post("/users/admins", headers=auth_headers, json=admin_payload())

    assert response.status_code == 201, response.text
    assert response.json()["role"] == "admin"
    assert response.json()["registered_by_user_id"]

    # new admin can sign in
    assert login("new-admin@example.com", "SecurePassword123")


def test_duplicate_admin_email_rejected_case_insensitively(client, auth_headers):
    assert client.post("/users/admins", headers=auth_headers, json=admin_payload()).status_code == 201

    duplicate = client.post(
        "/users/admins",
        headers=auth_headers,
        json=admin_payload(email="NEW-ADMIN@example.com"),
    )
    assert duplicate.status_code == 409


def test_admin_creation_requires_authentication(client):
    assert client.post("/users/admins", json=admin_payload()).status_code == 401


def test_agent_cannot_create_admin(client, auth_headers, make_point, make_agent):
    point = make_point(auth_headers)
    agent = make_agent(auth_headers, point["collection_point_id"])

    response = client.post("/users/admins", headers=agent["headers"], json=admin_payload())
    assert response.status_code == 403


def test_admin_creation_validates_password(client, auth_headers):
    response = client.post("/users/admins", headers=auth_headers, json=admin_payload(password="short"))
    assert response.status_code == 422


def test_users_me_returns_current_user(client, auth_headers):
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "admin@sulwe.com"
