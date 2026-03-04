from pathlib import Path
from unittest.mock import MagicMock, patch
import json

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import app.database as database
from app.ai import parse_ai_response
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


# --- Part 8: /api/ai/test ---

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
        body = resp.text
        assert "sk-or-" not in body
        assert "OPENROUTER_API_KEY" not in body


# --- Part 9: /api/ai/chat ---

async def test_chat_sends_board_context(authed_client: AsyncClient):
    """Verify board JSON is included in the system prompt sent to the AI."""
    with patch("app.ai.get_ai_client") as mock_get_client:
        mock_client = MagicMock()
        ai_response = json.dumps({"message": "Hello! I can see your board.", "board_updates": None})
        mock_client.chat.completions.create.return_value = _mock_completion(ai_response)
        mock_get_client.return_value = mock_client

        resp = await authed_client.post("/api/ai/chat", json={"message": "Hi", "history": []})
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Hello! I can see your board."
        assert data["board_updated"] is False

        # Check system prompt contains board data
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        messages = call_kwargs["messages"]
        system_msg = messages[0]
        assert system_msg["role"] == "system"
        assert "Backlog" in system_msg["content"]
        assert "columns" in system_msg["content"]


async def test_chat_without_board_updates(authed_client: AsyncClient):
    """AI response with message only, no board changes."""
    with patch("app.ai.get_ai_client") as mock_get_client:
        mock_client = MagicMock()
        ai_response = json.dumps({"message": "Your board has 5 columns."})
        mock_client.chat.completions.create.return_value = _mock_completion(ai_response)
        mock_get_client.return_value = mock_client

        resp = await authed_client.post("/api/ai/chat", json={"message": "How many columns?", "history": []})
        assert resp.status_code == 200
        data = resp.json()
        assert "5 columns" in data["message"]
        assert data["board_updated"] is False


async def test_chat_creates_card(authed_client: AsyncClient):
    """AI response with card creation actually creates the card in the DB."""
    with patch("app.ai.get_ai_client") as mock_get_client:
        mock_client = MagicMock()
        ai_response = json.dumps({
            "message": "Created a card in Backlog.",
            "board_updates": {
                "cards_to_create": [{"column_title": "Backlog", "title": "AI created card", "details": "Made by AI"}]
            }
        })
        mock_client.chat.completions.create.return_value = _mock_completion(ai_response)
        mock_get_client.return_value = mock_client

        resp = await authed_client.post("/api/ai/chat", json={"message": "Create a card", "history": []})
        assert resp.status_code == 200
        data = resp.json()
        assert data["board_updated"] is True

    # Verify card exists in the board
    board_resp = await authed_client.get("/api/board")
    board = board_resp.json()
    all_titles = [card["title"] for card in board["cards"].values()]
    assert "AI created card" in all_titles


async def test_chat_deletes_card(authed_client: AsyncClient):
    """AI response with card deletion actually removes the card from the DB."""
    # First get the board to find a card ID
    board_resp = await authed_client.get("/api/board")
    board = board_resp.json()
    card_id = list(board["cards"].keys())[0]
    card_title = board["cards"][card_id]["title"]

    with patch("app.ai.get_ai_client") as mock_get_client:
        mock_client = MagicMock()
        ai_response = json.dumps({
            "message": f"Deleted {card_title}.",
            "board_updates": {
                "cards_to_delete": [{"card_id": card_id}]
            }
        })
        mock_client.chat.completions.create.return_value = _mock_completion(ai_response)
        mock_get_client.return_value = mock_client

        resp = await authed_client.post("/api/ai/chat", json={"message": "Delete it", "history": []})
        assert resp.status_code == 200
        assert resp.json()["board_updated"] is True

    # Verify card is gone
    board_resp = await authed_client.get("/api/board")
    board = board_resp.json()
    assert card_id not in board["cards"]


async def test_chat_moves_card(authed_client: AsyncClient):
    """AI response with card move changes the card's column."""
    board_resp = await authed_client.get("/api/board")
    board = board_resp.json()
    # Find a card in Backlog
    backlog_col = next(c for c in board["columns"] if c["title"] == "Backlog")
    card_id = backlog_col["cardIds"][0]

    with patch("app.ai.get_ai_client") as mock_get_client:
        mock_client = MagicMock()
        ai_response = json.dumps({
            "message": "Moved to In Progress.",
            "board_updates": {
                "cards_to_move": [{"card_id": card_id, "column_title": "In Progress", "position": 0}]
            }
        })
        mock_client.chat.completions.create.return_value = _mock_completion(ai_response)
        mock_get_client.return_value = mock_client

        resp = await authed_client.post("/api/ai/chat", json={"message": "Move it", "history": []})
        assert resp.status_code == 200
        assert resp.json()["board_updated"] is True

    # Verify card is now in In Progress
    board_resp = await authed_client.get("/api/board")
    board = board_resp.json()
    in_progress = next(c for c in board["columns"] if c["title"] == "In Progress")
    assert card_id in in_progress["cardIds"]


async def test_chat_requires_auth(client: AsyncClient):
    resp = await client.post("/api/ai/chat", json={"message": "Hi", "history": []})
    assert resp.status_code == 401


async def test_chat_history_is_forwarded(authed_client: AsyncClient):
    """Verify conversation history is included in the messages sent to the AI."""
    with patch("app.ai.get_ai_client") as mock_get_client:
        mock_client = MagicMock()
        ai_response = json.dumps({"message": "Got it."})
        mock_client.chat.completions.create.return_value = _mock_completion(ai_response)
        mock_get_client.return_value = mock_client

        history = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "First reply"},
        ]
        resp = await authed_client.post("/api/ai/chat", json={"message": "Second message", "history": history})
        assert resp.status_code == 200

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        messages = call_kwargs["messages"]
        # system + 2 history + 1 user = 4
        assert len(messages) == 4
        assert messages[1]["content"] == "First message"
        assert messages[2]["content"] == "First reply"
        assert messages[3]["content"] == "Second message"


# --- parse_ai_response unit tests ---

def test_parse_malformed_json():
    """Malformed AI output is handled gracefully."""
    result = parse_ai_response("This is not JSON at all")
    assert "message" in result
    assert result["board_updates"] is None


def test_parse_missing_message_field():
    result = parse_ai_response('{"foo": "bar"}')
    assert "message" in result
    assert result["board_updates"] is None


def test_parse_valid_no_updates():
    result = parse_ai_response('{"message": "Hello"}')
    assert result["message"] == "Hello"
    assert result["board_updates"] is None


def test_parse_valid_with_updates():
    raw = json.dumps({
        "message": "Done",
        "board_updates": {
            "cards_to_create": [{"column_title": "Backlog", "title": "New", "details": ""}]
        }
    })
    result = parse_ai_response(raw)
    assert result["message"] == "Done"
    assert result["board_updates"] is not None
    assert len(result["board_updates"]["cards_to_create"]) == 1
