from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import app.database as database
from app.main import app


@pytest_asyncio.fixture
async def authed_client(tmp_path: Path):
    db_path = tmp_path / "test.db"
    database.DB_PATH = db_path
    conn = database.get_connection(db_path)
    database.init_db(conn)
    conn.close()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        login = await c.post("/api/login", json={"username": "user", "password": "password"})
        c.cookies = login.cookies
        yield c


@pytest_asyncio.fixture
async def client(tmp_path: Path):
    db_path = tmp_path / "test.db"
    database.DB_PATH = db_path
    conn = database.get_connection(db_path)
    database.init_db(conn)
    conn.close()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _mock_completion(content: str) -> MagicMock:
    choice = MagicMock()
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]
    return response


async def test_ai_test_returns_response(authed_client: AsyncClient):
    with patch("app.ai.get_ai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_completion("4")
        mock_get_client.return_value = mock_client

        resp = await authed_client.get("/api/ai/test")
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert "4" in data["response"]

        # Verify the call structure
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "openai/gpt-oss-120b"
        messages = call_kwargs.kwargs["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert "2+2" in messages[0]["content"]


async def test_ai_test_requires_auth(client: AsyncClient):
    resp = await client.get("/api/ai/test")
    assert resp.status_code == 401


async def test_ai_key_not_in_response(authed_client: AsyncClient):
    with patch("app.ai.get_ai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_completion("4")
        mock_get_client.return_value = mock_client

        resp = await authed_client.get("/api/ai/test")
        # Ensure no API key leaks in the response body
        body = resp.text
        assert "sk-or-" not in body
        assert "OPENROUTER_API_KEY" not in body
