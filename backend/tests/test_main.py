import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_index_returns_html(client: AsyncClient):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")


async def test_health(client: AsyncClient):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_login_success(client: AsyncClient):
    resp = await client.post("/api/login", json={"username": "user", "password": "password"})
    assert resp.status_code == 200
    assert resp.json() == {"username": "user"}
    assert "session" in resp.cookies


async def test_login_wrong_credentials(client: AsyncClient):
    resp = await client.post("/api/login", json={"username": "user", "password": "wrong"})
    assert resp.status_code == 401
    assert resp.json()["error"] == "Invalid credentials"


async def test_me_with_valid_session(client: AsyncClient):
    login = await client.post("/api/login", json={"username": "user", "password": "password"})
    resp = await client.get("/api/me", cookies=login.cookies)
    assert resp.status_code == 200
    assert resp.json() == {"username": "user"}


async def test_me_without_session(client: AsyncClient):
    resp = await client.get("/api/me")
    assert resp.status_code == 401


async def test_logout_clears_session(client: AsyncClient):
    login = await client.post("/api/login", json={"username": "user", "password": "password"})
    resp = await client.post("/api/logout", cookies=login.cookies)
    assert resp.status_code == 200
    # After logout, /api/me should reject
    me_resp = await client.get("/api/me")
    assert me_resp.status_code == 401
