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
    assert "Hello World" in resp.text
    assert resp.headers["content-type"].startswith("text/html")


async def test_health(client: AsyncClient):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
