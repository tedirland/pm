from pathlib import Path

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import app.database as database
from app.main import app


@pytest_asyncio.fixture
async def client(tmp_path: Path):
    """Unauthenticated test client with fresh DB."""
    db_path = tmp_path / "test.db"
    database.DB_PATH = db_path
    conn = database.get_connection(db_path)
    database.init_db(conn)
    # Seed a legacy user for backward compat tests
    database.ensure_user(conn, "user")
    conn.close()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def authed_client(tmp_path: Path):
    """Authenticated test client with fresh DB and logged-in session."""
    db_path = tmp_path / "test.db"
    database.DB_PATH = db_path
    conn = database.get_connection(db_path)
    database.init_db(conn)
    conn.close()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        # Register a test user
        resp = await c.post("/api/register", json={"username": "testuser", "password": "testpass123"})
        c.cookies = resp.cookies
        yield c


async def login_legacy_user(client: AsyncClient) -> dict:
    """Login as the legacy 'user' account. Returns cookies dict."""
    resp = await client.post("/api/login", json={"username": "user", "password": "password"})
    return dict(resp.cookies)
