from uuid import uuid4


def farmer_payload(point_id, **overrides):
    payload = {
        "first_name": "Jean",
        "last_name": "Farmer",
        "phone_number": "+250788123456",
        "collection_point_id": point_id,
    }
    payload.update(overrides)
    return payload


def test_farmer_registration_sends_confirmation_sms(client, auth_headers, make_point, outbox):
    point = make_point(auth_headers)

    response = client.post("/users/farmers", headers=auth_headers, json=farmer_payload(point["collection_point_id"]))

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["sms_sent"] is True
    assert body["farmer"]["role"] == "farmer"
    assert body["farmer"]["phone_number"] == "+250788123456"
    assert outbox.sms[0]["phone_number"] == "+250788123456"
    assert "created successfully" in outbox.sms[0]["message"].lower()
    assert "PIN" not in outbox.sms[0]["message"]


def test_farmer_remains_registered_if_sms_fails(client, auth_headers, make_point, outbox):
    outbox.sms_result = False
    point = make_point(auth_headers)

    response = client.post("/users/farmers", headers=auth_headers, json=farmer_payload(point["collection_point_id"]))
    assert response.status_code == 201, response.text
    assert response.json()["sms_sent"] is False


def test_farmer_registration_survives_sms_exception(client, auth_headers, make_point, monkeypatch):
    from services import user_service

    def boom(phone, message):
        raise RuntimeError("gateway down")

    monkeypatch.setattr(user_service, "send_sms", boom)
    point = make_point(auth_headers)

    response = client.post("/users/farmers", headers=auth_headers, json=farmer_payload(point["collection_point_id"]))
    assert response.status_code == 201
    assert response.json()["sms_sent"] is False


def test_duplicate_farmer_phone_rejected(client, auth_headers, make_point):
    point_id = make_point(auth_headers)["collection_point_id"]
    assert client.post("/users/farmers", headers=auth_headers, json=farmer_payload(point_id)).status_code == 201

    duplicate = client.post(
        "/users/farmers",
        headers=auth_headers,
        json=farmer_payload(point_id, id_number="RW-7654321"),
    )
    assert duplicate.status_code == 409, duplicate.text


def test_agent_can_register_farmer_at_own_point(client, auth_headers, make_point, make_agent):
    point = make_point(auth_headers)
    agent = make_agent(auth_headers, point["collection_point_id"])

    response = client.post(
        "/users/farmers",
        headers=agent["headers"],
        json=farmer_payload(point["collection_point_id"]),
    )
    assert response.status_code == 201, response.text
    assert response.json()["farmer"]["registered_by_user_id"] == agent["agent"]["user_id"]


def test_agent_cannot_register_farmer_at_another_point(client, auth_headers, make_point, make_agent):
    assigned = make_point(auth_headers, "Assigned Point")
    other = make_point(auth_headers, "Other Point")
    agent = make_agent(auth_headers, assigned["collection_point_id"], email="agent2@example.com")

    response = client.post(
        "/users/farmers",
        headers=agent["headers"],
        json=farmer_payload(other["collection_point_id"]),
    )
    assert response.status_code == 403, response.text


def test_farmer_registration_unknown_point_returns_404(client, auth_headers):
    response = client.post("/users/farmers", headers=auth_headers, json=farmer_payload(str(uuid4())))
    assert response.status_code == 404


def test_farmer_registration_foreign_point_returns_404(client, auth_headers, other_auth_headers, make_point):
    foreign = make_point(other_auth_headers, "Foreign Point")
    response = client.post(
        "/users/farmers",
        headers=auth_headers,
        json=farmer_payload(foreign["collection_point_id"]),
    )
    assert response.status_code == 404


def test_farmer_registration_inactive_point_returns_409(client, auth_headers, make_point):
    point = make_point(auth_headers)
    client.delete(f"/collection-points/{point['collection_point_id']}", headers=auth_headers)

    response = client.post("/users/farmers", headers=auth_headers, json=farmer_payload(point["collection_point_id"]))
    assert response.status_code == 409


def test_farmer_registration_validates_phone(client, auth_headers, make_point):
    point_id = make_point(auth_headers)["collection_point_id"]

    bad_phone = client.post(
        "/users/farmers",
        headers=auth_headers,
        json=farmer_payload(point_id, phone_number="0788123456"),
    )

    assert bad_phone.status_code == 422


def test_farmer_registration_requires_authentication(client):
    assert client.post("/users/farmers", json={}).status_code == 401


def test_farmer_cannot_log_in_with_email_password(client, auth_headers, make_point):
    point_id = make_point(auth_headers)["collection_point_id"]
    client.post("/users/farmers", headers=auth_headers, json=farmer_payload(point_id))

    response = client.post("/auth/login", json={"email": "farmer@example.com", "password": "SomePassword123"})
    assert response.status_code in {401, 403}
