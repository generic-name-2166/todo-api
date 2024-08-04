from fastapi.testclient import TestClient
import pytest

from todo_api.main import app


type MockUser = dict[str, str]


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def mock_user() -> MockUser:
    return {"username": "username", "password": "password"}


def test_unauthorized(client: TestClient, mock_user: MockUser) -> None:
    response = client.get("/user")
    assert response.status_code == 401
    response = client.post("/token", data=mock_user)


def login(client: TestClient, mock_user: MockUser) -> dict[str, str]:
    """Returns authorization header"""
    response = client.post("/token", data=mock_user)
    assert response.status_code == 200
    auth = response.json()
    assert auth["token_type"] == "bearer"
    access_token: str = auth["access_token"]
    assert isinstance(access_token, str)

    headers = {"Authorization": f"Bearer {access_token}"}
    return headers


def create_mock_user(client: TestClient, mock_user: MockUser) -> None:
    response = client.post("/user", json=mock_user)
    assert response.status_code == 200


def delete_mock_user(client: TestClient, headers: dict[str, str]) -> None:
    response = client.delete("/user", headers=headers)
    assert response.status_code == 200


def test_user(client: TestClient, mock_user: MockUser) -> None:
    create_mock_user(client, mock_user)
    token = login(client, mock_user)

    response = client.get("/user", headers=token)
    assert response.status_code == 200
    user = response.json()
    assert user["username"] == mock_user["username"]

    delete_mock_user(client, token)


def test_invalid_token(client: TestClient, mock_user: MockUser) -> None:
    create_mock_user(client, mock_user)
    token = login(client, mock_user)

    headers = {"Authorization": "Bearer invalid"}
    response = client.get("/user", headers=headers)
    assert response.status_code == 401

    delete_mock_user(client, token)


def test_invalid_password(client: TestClient, mock_user: MockUser) -> None:
    create_mock_user(client, mock_user)
    token = login(client, mock_user)

    invalid = mock_user.copy()
    invalid["password"] = "invalid"
    response = client.post("/token", data=invalid)
    assert response.status_code == 401

    delete_mock_user(client, token)


def test_duplicate_name(client: TestClient, mock_user: MockUser) -> None:
    create_mock_user(client, mock_user)
    token = login(client, mock_user)

    response = client.post("/user", json=mock_user)
    assert response.status_code == 409

    delete_mock_user(client, token)


def test_duplicate_name_update(client: TestClient, mock_user: MockUser) -> None:
    create_mock_user(client, mock_user)
    token = login(client, mock_user)

    response = client.put("/user", json="johndoe", headers=token)
    assert response.status_code == 409

    delete_mock_user(client, token)


def test_tasks(client: TestClient, mock_user: MockUser) -> None:
    create_mock_user(client, mock_user)
    token = login(client, mock_user)
    try:
        response = client.get("/tasks", headers=token)
        assert response.status_code == 200
        assert response.json() == []
    finally:
        delete_mock_user(client, token)


def test_creating_task(client: TestClient, mock_user: MockUser) -> None:
    create_mock_user(client, mock_user)
    token = login(client, mock_user)
    try:
        body = {"name": "test"}
        response = client.post("/tasks", json=body, headers=token)
        assert response.status_code == 200
    finally:
        delete_mock_user(client, token)


def test_getting_task(client: TestClient, mock_user: MockUser) -> None:
    create_mock_user(client, mock_user)
    token = login(client, mock_user)
    try:
        body = {"name": "test"}
        response = client.post("/tasks", json=body, headers=token)
        assert response.status_code == 200

        response = client.get("/tasks", headers=token)
        assert response.status_code == 200
        task = response.json()[0]
        task_id = task["id"]

        response = client.get(f"/tasks/{task_id}", headers=token)
        assert response.status_code == 200
        assert task == response.json()
    finally:
        delete_mock_user(client, token)


def test_nonexistent_task(client: TestClient, mock_user: MockUser) -> None:
    create_mock_user(client, mock_user)
    token = login(client, mock_user)
    try:
        body = {"name": "test"}
        response = client.post("/tasks", json=body, headers=token)
        assert response.status_code == 200

        response = client.get("/tasks", headers=token)
        assert response.status_code == 200
        task = response.json()[0]
        task_id = task["id"]

        response = client.get(f"/tasks/{task_id + 1}", headers=token)
        assert response.status_code == 404

        response = client.put(
            f"/tasks/{task_id + 1}", json={"name": "invalid"}, headers=token
        )
        assert response.status_code == 404

        response = client.delete(f"/tasks/{task_id + 1}", headers=token)
        assert response.status_code == 404
    finally:
        delete_mock_user(client, token)


def test_updating_task(client: TestClient, mock_user: MockUser) -> None:
    create_mock_user(client, mock_user)
    token = login(client, mock_user)
    try:
        body = {"name": "test"}
        response = client.post("/tasks", json=body, headers=token)
        assert response.status_code == 200

        response = client.get("/tasks", headers=token)
        assert response.status_code == 200
        task = response.json()[0]
        task_id = task["id"]

        body = {"name": "test1"}
        response = client.put(f"/tasks/{task_id}", json=body, headers=token)
        assert response.status_code == 200
    finally:
        delete_mock_user(client, token)


def test_deleting_task(client: TestClient, mock_user: MockUser) -> None:
    create_mock_user(client, mock_user)
    token = login(client, mock_user)
    try:
        body = {"name": "test"}
        response = client.post("/tasks", json=body, headers=token)
        assert response.status_code == 200

        response = client.get("/tasks", headers=token)
        assert response.status_code == 200
        task = response.json()[0]
        task_id = task["id"]

        response = client.delete(f"/tasks/{task_id}", headers=token)
        assert response.status_code == 200
    finally:
        delete_mock_user(client, token)


def test_permissions(client: TestClient, mock_user: MockUser) -> None:
    create_mock_user(client, mock_user)
    token = login(client, mock_user)
    try:
        body = {"name": "test"}
        response = client.post("/tasks", json=body, headers=token)
        assert response.status_code == 200

        response = client.get("/tasks", headers=token)
        assert response.status_code == 200
        task = response.json()[0]
        task_id = task["id"]

        response = client.get(f"/tasks/{task_id}/permissions", headers=token)
        assert response.status_code == 200
        assert response.json() == []
    finally:
        delete_mock_user(client, token)


def test_permissions_nonexistent(client: TestClient, mock_user: MockUser) -> None:
    create_mock_user(client, mock_user)
    token = login(client, mock_user)
    try:
        body = {"name": "test"}
        response = client.post("/tasks", json=body, headers=token)
        assert response.status_code == 200

        response = client.get("/tasks", headers=token)
        assert response.status_code == 200
        task = response.json()[0]
        task_id = task["id"]

        response = client.get(f"/tasks/{task_id + 1}/permissions", headers=token)
        assert response.status_code == 404

        body = {"recepient_id": 1, "perm_type": "read"}
        response = client.post(
            f"/tasks/{task_id + 1}/permissions", json=body, headers=token
        )
        assert response.status_code == 404
    finally:
        delete_mock_user(client, token)


def test_adding_permission(client: TestClient, mock_user: MockUser) -> None:
    create_mock_user(client, mock_user)
    token = login(client, mock_user)
    try:
        body = {"name": "test"}
        response = client.post("/tasks", json=body, headers=token)
        assert response.status_code == 200

        response = client.get("/tasks", headers=token)
        assert response.status_code == 200
        task = response.json()[0]
        task_id = task["id"]

        body = {"recepient_id": 1, "perm_type": "read"}
        response = client.post(
            f"/tasks/{task_id}/permissions", json=body, headers=token
        )
        assert response.status_code == 200
    finally:
        delete_mock_user(client, token)


def test_removing_permission(client: TestClient, mock_user: MockUser) -> None:
    create_mock_user(client, mock_user)
    token = login(client, mock_user)
    try:
        body = {"name": "test"}
        response = client.post("/tasks", json=body, headers=token)
        assert response.status_code == 200

        response = client.get("/tasks", headers=token)
        assert response.status_code == 200
        task = response.json()[0]
        task_id = task["id"]

        body = {"recepient_id": 1, "perm_type": "read"}
        url = f"/tasks/{task_id}/permissions"
        response = client.post(url, json=body, headers=token)
        assert response.status_code == 200

        response = client.delete(url, params=body, headers=token)
        assert response.status_code == 200
    finally:
        delete_mock_user(client, token)
