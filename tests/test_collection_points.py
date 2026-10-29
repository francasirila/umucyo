from uuid import uuid4


def test_create_collection_point(client, auth_headers):
    response = client.post(
        "/collection-points/",
        headers=auth_headers,
        json={"collection_name": "North Point"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["collection_name"] == "North Point"
    assert body["status"] == "active"
    assert body["collection_point_id"]
    assert "location" not in body


def test_collection_name_is_trimmed(client, auth_headers):
    response = client.post("/collection-points/", headers=auth_headers, json={"collection_name": "  Padded  "})
    assert response.status_code == 201
    assert response.json()["collection_name"] == "Padded"


def test_duplicate_collection_point_rejected_case_insensitively(client, auth_headers, make_point):
    make_point(auth_headers, "North Point")

    duplicate = client.post("/collection-points/", headers=auth_headers, json={"collection_name": "north point"})
    assert duplicate.status_code == 409, duplicate.text


def test_same_name_allowed_in_different_cooperatives(client, auth_headers, other_auth_headers, make_point):
    make_point(auth_headers, "Shared Name")
    assert make_point(other_auth_headers, "Shared Name")["collection_point_id"]


def test_collection_name_validation(client, auth_headers):
    too_short = client.post("/collection-points/", headers=auth_headers, json={"collection_name": "A"})
    whitespace = client.post("/collection-points/", headers=auth_headers, json={"collection_name": "   "})
    assert too_short.status_code == 422
    assert whitespace.status_code == 422


def test_list_collection_points(client, auth_headers, make_point):
    make_point(auth_headers, "North Point")
    make_point(auth_headers, "South Point")

    response = client.get("/collection-points/", headers=auth_headers)

    assert response.status_code == 200, response.text
    assert [p["collection_name"] for p in response.json()] == ["North Point", "South Point"]


def test_list_filters_by_status(client, auth_headers, make_point):
    make_point(auth_headers, "Active Point")
    inactive = make_point(auth_headers, "Inactive Point")
    client.delete(f"/collection-points/{inactive['collection_point_id']}", headers=auth_headers)

    active = client.get("/collection-points/?status=active", headers=auth_headers).json()
    inactive_list = client.get("/collection-points/?status=inactive", headers=auth_headers).json()

    assert [p["collection_name"] for p in active] == ["Active Point"]
    assert [p["collection_name"] for p in inactive_list] == ["Inactive Point"]


def test_list_only_shows_own_cooperative(client, auth_headers, other_auth_headers, make_point):
    make_point(auth_headers, "Mine")
    make_point(other_auth_headers, "Theirs")

    names = [p["collection_name"] for p in client.get("/collection-points/", headers=auth_headers).json()]
    assert names == ["Mine"]


def test_get_collection_point_by_id(client, auth_headers, make_point):
    point_id = make_point(auth_headers)["collection_point_id"]

    response = client.get(f"/collection-points/{point_id}", headers=auth_headers)
    assert response.status_code == 200, response.text
    assert response.json()["collection_point_id"] == point_id


def test_get_unknown_collection_point_returns_404(client, auth_headers):
    assert client.get(f"/collection-points/{uuid4()}", headers=auth_headers).status_code == 404


def test_get_foreign_collection_point_returns_404(client, auth_headers, other_auth_headers, make_point):
    foreign = make_point(other_auth_headers, "Foreign")
    response = client.get(f"/collection-points/{foreign['collection_point_id']}", headers=auth_headers)
    assert response.status_code == 404


def test_invalid_collection_point_id_returns_422(client, auth_headers):
    assert client.get("/collection-points/not-a-uuid", headers=auth_headers).status_code == 422


def test_update_collection_point_name(client, auth_headers, make_point):
    point_id = make_point(auth_headers)["collection_point_id"]

    response = client.patch(
        f"/collection-points/{point_id}",
        headers=auth_headers,
        json={"collection_name": "Renamed"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["collection_name"] == "Renamed"


def test_update_collection_point_status(client, auth_headers, make_point):
    point_id = make_point(auth_headers)["collection_point_id"]

    response = client.patch(f"/collection-points/{point_id}", headers=auth_headers, json={"status": "inactive"})
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "inactive"


def test_update_to_duplicate_name_rejected(client, auth_headers, make_point):
    make_point(auth_headers, "First")
    second = make_point(auth_headers, "Second")

    response = client.patch(
        f"/collection-points/{second['collection_point_id']}",
        headers=auth_headers,
        json={"collection_name": "first"},
    )
    assert response.status_code == 409


def test_update_with_same_name_is_allowed(client, auth_headers, make_point):
    point = make_point(auth_headers, "Same")
    response = client.patch(
        f"/collection-points/{point['collection_point_id']}",
        headers=auth_headers,
        json={"collection_name": "Same"},
    )
    assert response.status_code == 200


def test_update_with_no_changes_rejected(client, auth_headers, make_point):
    point_id = make_point(auth_headers)["collection_point_id"]
    assert client.patch(f"/collection-points/{point_id}", headers=auth_headers, json={}).status_code == 422


def test_delete_deactivates_and_is_idempotent(client, auth_headers, make_point):
    point_id = make_point(auth_headers)["collection_point_id"]

    assert client.delete(f"/collection-points/{point_id}", headers=auth_headers).status_code == 204
    assert client.delete(f"/collection-points/{point_id}", headers=auth_headers).status_code == 204

    fetched = client.get(f"/collection-points/{point_id}", headers=auth_headers)
    assert fetched.json()["status"] == "inactive"


def test_collection_point_routes_require_authentication(client):
    assert client.post("/collection-points/", json={"collection_name": "Nope"}).status_code == 401
    assert client.get("/collection-points/").status_code == 401


def test_agent_sees_only_own_point_and_cannot_manage(client, auth_headers, make_point, make_agent):
    own = make_point(auth_headers, "Own Point")
    other = make_point(auth_headers, "Other Point")
    agent = make_agent(auth_headers, own["collection_point_id"])

    listed = client.get("/collection-points/", headers=agent["headers"]).json()
    assert [p["collection_name"] for p in listed] == ["Own Point"]

    assert client.get(f"/collection-points/{own['collection_point_id']}", headers=agent["headers"]).status_code == 200
    assert client.get(f"/collection-points/{other['collection_point_id']}", headers=agent["headers"]).status_code == 404

    assert client.post("/collection-points/", headers=agent["headers"], json={"collection_name": "Nope"}).status_code == 403
    assert (
        client.patch(
            f"/collection-points/{own['collection_point_id']}", headers=agent["headers"], json={"collection_name": "Hack"}
        ).status_code
        == 403
    )
    assert client.delete(f"/collection-points/{own['collection_point_id']}", headers=agent["headers"]).status_code == 403
