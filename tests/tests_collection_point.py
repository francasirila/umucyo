def create_point(client, headers, name="North Point", location="Musanze"):
    response = client.post(
        "/collection-points/",
        headers=headers,
        json={
            "collection_name": name,
            "location": location,
        },
    )

    assert response.status_code == 201, response.text
    return response.json()


def test_create_collection_point(client, auth_headers):
    response = client.post(
        "/collection-points/",
        headers=auth_headers,
        json={
            "collection_name": "North Point",
            "location": "Musanze",
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()

    assert body["collection_name"] == "North Point"
    assert body["location"] == "Musanze"
    assert body["collection_point_id"]


def test_duplicate_collection_point_rejected(client, auth_headers):
    payload = {
        "collection_name": "North Point",
        "location": "Musanze",
    }

    first = client.post(
        "/collection-points/",
        headers=auth_headers,
        json=payload,
    )
    assert first.status_code == 201, first.text

    duplicate = client.post(
        "/collection-points/",
        headers=auth_headers,
        json=payload,
    )

    assert duplicate.status_code == 409, duplicate.text


def test_list_collection_points(client, auth_headers):
    create_point(client, auth_headers, "North Point", "Musanze")
    create_point(client, auth_headers, "South Point", "Huye")

    response = client.get(
        "/collection-points/",
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text

    names = {point["collection_name"] for point in response.json()}

    assert "North Point" in names
    assert "South Point" in names


def test_get_collection_point_by_id(client, auth_headers):
    point = create_point(client, auth_headers)
    point_id = point["collection_point_id"]

    response = client.get(
        f"/collection-points/{point_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()["collection_point_id"] == point_id


def test_update_collection_point(client, auth_headers):
    point = create_point(client, auth_headers)
    point_id = point["collection_point_id"]

    response = client.patch(
        f"/collection-points/{point_id}",
        headers=auth_headers,
        json={"location": "Huye"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["location"] == "Huye"


def test_delete_collection_point(client, auth_headers):
    point = create_point(client, auth_headers)
    point_id = point["collection_point_id"]

    response = client.delete(
        f"/collection-points/{point_id}",
        headers=auth_headers,
    )

    assert response.status_code in {200, 204}


def test_collection_point_routes_require_authentication(client):
    payload = {
        "collection_name": "Unauthorised Point",
        "location": "Kigali",
    }

    response = client.post("/collection-points/", json=payload)

    assert response.status_code == 401


def test_invalid_collection_point_id_returns_client_error(
    client,
    auth_headers,
):
    response = client.get(
        "/collection-points/not-a-uuid",
        headers=auth_headers,
    )

    assert response.status_code == 422
