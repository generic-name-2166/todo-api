from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
import pytest

from todo_api.main import app


type MockUser = dict[str, str]


@pytest.fixture(scope="module")
async def client():
    async with (
        LifespanManager(app) as manager,
        AsyncClient(
            transport=ASGITransport(app=manager.app), base_url="http://localhost:8000"
        ) as c,
    ):
        assert isinstance(c, AsyncClient)
        yield c


@pytest.fixture(scope="module")
def mock_user() -> MockUser:
    return {"username": "username", "password": "password"}


@pytest.mark.asyncio
async def test_unauthorized(client: AsyncClient) -> None:
    assert isinstance(client, AsyncClient)
    response = await client.get("/user")
    assert response.status_code == 401


async def login(client: AsyncClient, mock_user: MockUser) -> dict[str, str]:
    """Returns authorization header"""
    response = await client.post("/token", data=mock_user)
    assert response.status_code == 200, response.json()
    auth = response.json()
    assert auth["token_type"] == "bearer"
    access_token: str = auth["access_token"]
    assert isinstance(access_token, str)

    headers = {"Authorization": f"Bearer {access_token}"}
    return headers


async def create_mock_user(client: AsyncClient, mock_user: MockUser) -> None:
    response = await client.post("/user", json=mock_user)
    assert response.status_code == 200


async def delete_mock_user(client: AsyncClient, headers: dict[str, str]) -> None:
    response = await client.delete("/user", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_user(client: AsyncClient, mock_user: MockUser) -> None:
    await create_mock_user(client, mock_user)
    token = await login(client, mock_user)

    response = await client.get("/user", headers=token)
    assert response.status_code == 200
    user = response.json()
    assert user["username"] == mock_user["username"]

    await delete_mock_user(client, token)


@pytest.mark.asyncio
async def test_invalid_token(client: AsyncClient, mock_user: MockUser) -> None:
    await create_mock_user(client, mock_user)
    token = await login(client, mock_user)

    headers = {"Authorization": "Bearer invalid"}
    response = await client.get("/user", headers=headers)
    assert response.status_code == 401

    await delete_mock_user(client, token)


@pytest.mark.asyncio
async def test_invalid_password(client: AsyncClient, mock_user: MockUser) -> None:
    await create_mock_user(client, mock_user)
    token = await login(client, mock_user)

    invalid = mock_user.copy()
    invalid["password"] = "invalid"
    response = await client.post("/token", data=invalid)
    assert response.status_code == 401

    await delete_mock_user(client, token)


@pytest.mark.asyncio
async def test_duplicate_name(client: AsyncClient, mock_user: MockUser) -> None:
    await create_mock_user(client, mock_user)
    token = await login(client, mock_user)

    response = await client.post("/user", json=mock_user)
    assert response.status_code == 409

    await delete_mock_user(client, token)


@pytest.mark.asyncio
async def test_duplicate_name_update(client: AsyncClient, mock_user: MockUser) -> None:
    await create_mock_user(client, mock_user)
    token = await login(client, mock_user)
    try:
        # Requres a johndoe user to be already in the database
        # TODO add this as a before all
        response = await client.put("/user", json="johndoe", headers=token)
        assert response.status_code == 409
    finally:
        await delete_mock_user(client, token)


@pytest.mark.asyncio
async def test_tasks(client: AsyncClient, mock_user: MockUser) -> None:
    await create_mock_user(client, mock_user)
    token = await login(client, mock_user)
    try:
        response = await client.get("/tasks", headers=token)
        assert response.status_code == 200
        assert response.json() == []
    finally:
        await delete_mock_user(client, token)


@pytest.mark.asyncio
async def test_creating_task(client: AsyncClient, mock_user: MockUser) -> None:
    await create_mock_user(client, mock_user)
    token = await login(client, mock_user)
    try:
        body = {"title": "test", "contents": ""}
        response = await client.post("/tasks", json=body, headers=token)
        assert response.status_code == 200
    finally:
        await delete_mock_user(client, token)


@pytest.mark.asyncio
async def test_getting_task(client: AsyncClient, mock_user: MockUser) -> None:
    await create_mock_user(client, mock_user)
    token = await login(client, mock_user)
    try:
        body = {"title": "test", "contents": ""}
        response = await client.post("/tasks", json=body, headers=token)
        assert response.status_code == 200

        response = await client.get("/tasks", headers=token)
        assert response.status_code == 200
        task = response.json()[0]
        task_id = task["id"]

        response = await client.get(f"/tasks/{task_id}", headers=token)
        assert response.status_code == 200
        assert task == response.json()
    finally:
        await delete_mock_user(client, token)


@pytest.mark.asyncio
async def test_nonexistent_task(client: AsyncClient, mock_user: MockUser) -> None:
    await create_mock_user(client, mock_user)
    token = await login(client, mock_user)
    try:
        body = {"title": "test", "contents": ""}
        response = await client.post("/tasks", json=body, headers=token)
        assert response.status_code == 200

        response = await client.get("/tasks", headers=token)
        assert response.status_code == 200
        task = response.json()[0]
        task_id = task["id"]

        response = await client.get(f"/tasks/{task_id + 1}", headers=token)
        assert response.status_code == 404

        response = await client.put(
            f"/tasks/{task_id + 1}",
            json={"title": "invalid", "contents": ""},
            headers=token,
        )
        assert response.status_code == 404

        response = await client.delete(f"/tasks/{task_id + 1}", headers=token)
        assert response.status_code == 404
    finally:
        await delete_mock_user(client, token)


@pytest.mark.asyncio
async def test_updating_task(client: AsyncClient, mock_user: MockUser) -> None:
    await create_mock_user(client, mock_user)
    token = await login(client, mock_user)
    try:
        body = {"title": "test", "contents": ""}
        response = await client.post("/tasks", json=body, headers=token)
        assert response.status_code == 200

        response = await client.get("/tasks", headers=token)
        assert response.status_code == 200
        task = response.json()[0]
        task_id = task["id"]

        body = {"title": "test1", "contents": ""}
        response = await client.put(f"/tasks/{task_id}", json=body, headers=token)
        assert response.status_code == 200
    finally:
        await delete_mock_user(client, token)


@pytest.mark.asyncio
async def test_deleting_task(client: AsyncClient, mock_user: MockUser) -> None:
    await create_mock_user(client, mock_user)
    token = await login(client, mock_user)
    try:
        body = {"title": "test", "contents": ""}
        response = await client.post("/tasks", json=body, headers=token)
        assert response.status_code == 200

        response = await client.get("/tasks", headers=token)
        assert response.status_code == 200
        task = response.json()[0]
        task_id = task["id"]

        response = await client.delete(f"/tasks/{task_id}", headers=token)
        assert response.status_code == 200
    finally:
        await delete_mock_user(client, token)


type JsonTag = dict[str, int | str]
type JsonTask = dict[str, int | str | list[JsonTag]]
type JsonNewTask = dict[str, int | str | list[str]]


@pytest.mark.asyncio
async def test_searching_task_by_tag(client: AsyncClient, mock_user: MockUser) -> None:
    await create_mock_user(client, mock_user)
    token = await login(client, mock_user)
    try:
        body: JsonNewTask = {"title": "test", "contents": "", "tags": ["Tag"]}
        response = await client.post("/tasks", json=body, headers=token)
        assert response.status_code == 200

        response = await client.get("/tasks/search/A", headers=token)
        assert response.status_code == 200
        tasks: list[JsonTask] = response.json()
        assert isinstance(tasks, list)
        assert len(tasks) == 0

        response = await client.get("/tasks/search/T", headers=token)
        assert response.status_code == 200
        tasks: list[JsonTask] = response.json()
        assert isinstance(tasks, list)
        assert len(tasks) == 1
        assert tasks[0]["title"] == "test"
    finally:
        await delete_mock_user(client, token)
