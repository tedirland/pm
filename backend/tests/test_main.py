from httpx import AsyncClient

from tests.conftest import login_legacy_user


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


async def test_me_with_valid_session(client: AsyncClient):
    cookies = await login_legacy_user(client)
    resp = await client.get("/api/me", cookies=cookies)
    assert resp.status_code == 200
    assert resp.json() == {"username": "user"}


async def test_me_without_session(client: AsyncClient):
    resp = await client.get("/api/me")
    assert resp.status_code == 401


async def test_logout_clears_session(client: AsyncClient):
    cookies = await login_legacy_user(client)
    resp = await client.post("/api/logout", cookies=cookies)
    assert resp.status_code == 200
    # After logout, /api/me should reject with the old cookie
    resp = await client.get("/api/me", cookies=cookies)
    assert resp.status_code == 401
