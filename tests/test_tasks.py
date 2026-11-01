from uuid import uuid4


def test_create_task_returns_created_task(task_client, task_payload):
    response = task_client.post("/tasks", json=task_payload)

    assert response.status_code == 201, response.text

    data = response.json()
    assert data["task_id"]
    assert data["cooperative_id"] == task_payload["cooperative_id"]
    assert data["created_by_user_id"] == task_payload["created_by_user_id"]
    assert data["assigned_to_user_id"] == task_payload["assigned_to_user_id"]
    assert data["description"] == task_payload["description"]
    assert data["priority"] == "normal"
    assert data["status"] == "open"
    assert data["completed_at"] is None
    assert data["created_at"] is not None


def test_create_task_rejects_unknown_cooperative(task_client, task_payload):
    task_payload["cooperative_id"] = str(uuid4())
    response = task_client.post("/tasks", json=task_payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Cooperative not found."


def test_create_task_rejects_empty_description(task_client, task_payload):
    task_payload["description"] = ""
    response = task_client.post("/tasks", json=task_payload)
    assert response.status_code == 422


def test_list_tasks_returns_created_tasks(task_client, task_payload):
    create_response = task_client.post("/tasks", json=task_payload)
    assert create_response.status_code == 201, create_response.text
    response = task_client.get("/tasks")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 1
    assert response.json()[0]["task_id"] == create_response.json()["task_id"]


def test_list_tasks_respects_limit(task_client, task_payload):
    first = task_client.post("/tasks", json=task_payload)
    assert first.status_code == 201, first.text
    second_payload = {
        **task_payload,
        "description": "Inspect tea collection records",
    }
    second = task_client.post("/tasks", json=second_payload)
    assert second.status_code == 201, second.text
    response = task_client.get("/tasks?skip=0&limit=1")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 1


def test_get_task_returns_task_by_id(task_client, task_payload):
    created = task_client.post("/tasks", json=task_payload)
    assert created.status_code == 201, created.text
    task_id = created.json()["task_id"]
    response = task_client.get(f"/tasks/{task_id}")
    assert response.status_code == 200, response.text
    assert response.json()["task_id"] == task_id
    assert response.json()["description"] == task_payload["description"]


def test_get_unknown_task_returns_404(task_client):
    response = task_client.get(f"/tasks/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found."


def test_update_task_description(task_client, task_payload):
    created = task_client.post("/tasks", json=task_payload)
    assert created.status_code == 201, created.text
    task_id = created.json()["task_id"]
    response = task_client.patch(
        f"/tasks/{task_id}",
        json={"description": "Verify tea delivery receipts"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["description"] == "Verify tea delivery receipts"


def test_completing_task_sets_completed_at(task_client, task_payload):
    created = task_client.post("/tasks", json=task_payload)
    assert created.status_code == 201, created.text
    task_id = created.json()["task_id"]

    response = task_client.patch(
        f"/tasks/{task_id}",
        json={"status": "completed"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "completed"
    assert response.json()["completed_at"] is not None


def test_reopening_completed_task_clears_completed_at(task_client, task_payload):
    created = task_client.post("/tasks", json=task_payload)
    assert created.status_code == 201, created.text
    task_id = created.json()["task_id"]

    completed = task_client.patch(
        f"/tasks/{task_id}",
        json={"status": "completed"},
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["completed_at"] is not None

    reopened = task_client.patch(
        f"/tasks/{task_id}",
        json={"status": "in_progress"},
    )

    assert reopened.status_code == 200, reopened.text
    assert reopened.json()["status"] == "in_progress"
    assert reopened.json()["completed_at"] is None


def test_update_unknown_task_returns_404(task_client):
    response = task_client.patch(
        f"/tasks/{uuid4()}",
        json={"description": "Updated tea task"},
    )

    assert response.status_code == 404


def test_delete_task_returns_204(task_client, task_payload):
    created = task_client.post("/tasks", json=task_payload)
    assert created.status_code == 201, created.text
    task_id = created.json()["task_id"]

    response = task_client.delete(f"/tasks/{task_id}")

    assert response.status_code == 204
    assert response.content == b""

    follow_up = task_client.get(f"/tasks/{task_id}")
    assert follow_up.status_code == 404


def test_delete_unknown_task_returns_404(task_client):
    response = task_client.delete(f"/tasks/{uuid4()}")
    assert response.status_code == 404
