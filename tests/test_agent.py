from uuid import uuid4


def agent_payload(point_id, **overrides):
    payload = {
        "first_name": "Agent",
        "last_name": "One",
        "email": "agent@example.com",
        "collection_point_id": point_id,
    }
    payload.update(overrides)
    return payload


def test_admin_can_register_agent_and_agent_can_set_password(client, auth_headers, make_point, make_agent, outbox):
    point = make_point(auth_headers)
    result = make_agent(auth_headers, point["collection_point_id"])

    assert result["agent"]["email"] == "agent@example.com"
    assert result["agent"]["role"] == "agent"
    assert result["agent"]["status"] == "pending"
    assert result["agent"]["collection_point_id"] == point["collection_point_id"]
    assert outbox.invitations[-1]["purpose"] == "invitation"

    me = client.get("/auth/me", headers=result["headers"])
    assert me.status_code == 200
    assert me.json()["status"] == "active"


def test_invitation_failure_does_not_block_registration(client, auth_headers, make_point, outbox):
    outbox.fail_invitation = True
    point = make_point(auth_headers)

    response = client.post("/users/agents", headers=auth_headers, json=agent_payload(point["collection_point_id"]))
    assert response.status_code == 201, response.text
    assert response.json()["invitation_sent"] is False


def test_pending_agent_cannot_log_in(client, auth_headers, make_point, make_agent):
    point = make_point(auth_headers)
    make_agent(auth_headers, point["collection_point_id"], activate=False)

    response = client.post("/auth/login", json={"email": "agent@example.com", "password": "AgentPassword123"})
    assert response.status_code == 401


def test_duplicate_agent_email_rejected(client, auth_headers, make_point, make_agent):
    point = make_point(auth_headers)
    make_agent(auth_headers, point["collection_point_id"])

    response = client.post(
        "/users/agents",
        headers=auth_headers,
        json=agent_payload(point["collection_point_id"], first_name="Another"),
    )
    assert response.status_code == 409, response.text


def test_agent_registration_requires_authentication(client):
    assert client.post("/users/agents", json={}).status_code == 401


def test_agent_cannot_register_other_agents(client, auth_headers, make_point, make_agent):
    point = make_point(auth_headers)
    agent = make_agent(auth_headers, point["collection_point_id"])

    response = client.post(
        "/users/agents",
        headers=agent["headers"],
        json=agent_payload(point["collection_point_id"], email="x@example.com"),
    )
    assert response.status_code == 403


def test_register_agent_unknown_point_returns_404(client, auth_headers):
    response = client.post("/users/agents", headers=auth_headers, json=agent_payload(str(uuid4())))
    assert response.status_code == 404


def test_register_agent_at_other_cooperative_point_returns_404(client, auth_headers, other_auth_headers, make_point):
    foreign_point = make_point(other_auth_headers, "Foreign Point")

    response = client.post(
        "/users/agents",
        headers=auth_headers,
        json=agent_payload(foreign_point["collection_point_id"]),
    )
    assert response.status_code == 404


def test_register_agent_at_inactive_point_returns_409(client, auth_headers, make_point):
    point = make_point(auth_headers)
    client.delete(f"/collection-points/{point['collection_point_id']}", headers=auth_headers)

    response = client.post("/users/agents", headers=auth_headers, json=agent_payload(point["collection_point_id"]))
    assert response.status_code == 409


def test_agent_registration_validates_email(client, auth_headers, make_point):
    point = make_point(auth_headers)
    response = client.post(
        "/users/agents",
        headers=auth_headers,
        json=agent_payload(point["collection_point_id"], email="nope"),
    )
    assert response.status_code == 422


def test_admin_can_update_agent_status(client, auth_headers, make_point, make_agent):
    point = make_point(auth_headers)
    agent = make_agent(auth_headers, point["collection_point_id"], activate=False)

    updated = client.patch(
        f"/users/agents/{agent['agent']['user_id']}",
        headers=auth_headers,
        json={"status": "inactive"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["status"] == "inactive"


def test_admin_can_update_agent_names(client, auth_headers, make_point, make_agent):
    point = make_point(auth_headers)
    agent = make_agent(auth_headers, point["collection_point_id"], activate=False)

    updated = client.patch(
        f"/users/agents/{agent['agent']['user_id']}",
        headers=auth_headers,
        json={"first_name": "  Renamed ", "last_name": "Person"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["first_name"] == "Renamed"
    assert updated.json()["last_name"] == "Person"


def test_update_agent_requires_changes(client, auth_headers, make_point, make_agent):
    point = make_point(auth_headers)
    agent = make_agent(auth_headers, point["collection_point_id"], activate=False)

    response = client.patch(f"/users/agents/{agent['agent']['user_id']}", headers=auth_headers, json={})
    assert response.status_code == 422


def test_update_unknown_agent_returns_404(client, auth_headers):
    response = client.patch(f"/users/agents/{uuid4()}", headers=auth_headers, json={"status": "inactive"})
    assert response.status_code == 404


def test_admin_id_is_not_updatable_as_agent(client, auth_headers):
    me = client.get("/auth/me", headers=auth_headers).json()
    response = client.patch(f"/users/agents/{me['user_id']}", headers=auth_headers, json={"status": "inactive"})
    assert response.status_code == 404


def test_other_cooperative_cannot_update_agent(client, auth_headers, other_auth_headers, make_point, make_agent):
    point = make_point(auth_headers)
    agent = make_agent(auth_headers, point["collection_point_id"], activate=False)

    response = client.patch(
        f"/users/agents/{agent['agent']['user_id']}",
        headers=other_auth_headers,
        json={"status": "inactive"},
    )
    assert response.status_code == 404


def test_agent_cannot_update_agents(client, auth_headers, make_point, make_agent):
    point = make_point(auth_headers)
    agent = make_agent(auth_headers, point["collection_point_id"])

    response = client.patch(
        f"/users/agents/{agent['agent']['user_id']}",
        headers=agent["headers"],
        json={"status": "inactive"},
    )
    assert response.status_code == 403


def test_deactivated_agent_is_locked_out(client, auth_headers, make_point, make_agent):
    point = make_point(auth_headers)
    agent = make_agent(auth_headers, point["collection_point_id"])

    client.patch(
        f"/users/agents/{agent['agent']['user_id']}",
        headers=auth_headers,
        json={"status": "inactive"},
    )

    assert client.get("/auth/me", headers=agent["headers"]).status_code == 403
    login = client.post("/auth/login", json={"email": "agent@example.com", "password": "AgentPassword123"})
    assert login.status_code == 403
