def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Umucyo API is running", "docs": "/docs"}


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_unknown_route_returns_404(client):
    assert client.get("/does-not-exist").status_code == 404


def test_service_errors_are_rendered_as_json_detail(client):
    response = client.post("/auth/login", json={"email": "ghost@example.com", "password": "Whatever123"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password."}


def test_all_expected_routes_are_registered(client):
    paths = set(client.app.openapi()["paths"])
    expected = {
        "/auth/login",
        "/auth/verify-otp",
        "/auth/resend-otp",
        "/auth/set-password",
        "/auth/me",
        "/auth/logout",
        "/users/me",
        "/users/admins",
        "/users/agents",
        "/users/agents/{agent_id}",
        "/users/farmers",
        "/collection-points/",
        "/collection-points/{point_id}",
    }
    assert expected <= paths
    assert "/users/ussd/authorize" not in paths
