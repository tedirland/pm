import tempfile
from pathlib import Path

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import app.database as database
from app.main import app


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


async def _login(client: AsyncClient) -> dict:
    resp = await client.post("/api/login", json={"username": "user", "password": "password"})
    return dict(resp.cookies)


# --- GET /api/board ---

async def test_board_requires_auth(client: AsyncClient):
    resp = await client.get("/api/board")
    assert resp.status_code == 401


async def test_board_returns_seeded_data(client: AsyncClient):
    cookies = await _login(client)
    resp = await client.get("/api/board", cookies=cookies)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["columns"]) == 5
    assert len(data["cards"]) == 8
    assert data["columns"][0]["title"] == "Backlog"
    assert len(data["columns"][0]["cardIds"]) == 2


async def test_board_card_order(client: AsyncClient):
    cookies = await _login(client)
    resp = await client.get("/api/board", cookies=cookies)
    data = resp.json()
    backlog_ids = data["columns"][0]["cardIds"]
    first_card = data["cards"][backlog_ids[0]]
    assert first_card["title"] == "Align roadmap themes"


# --- PUT /api/board/columns/:id ---

async def test_rename_column_requires_auth(client: AsyncClient):
    resp = await client.put("/api/board/columns/col-1", json={"title": "New"})
    assert resp.status_code == 401


async def test_rename_column(client: AsyncClient):
    cookies = await _login(client)
    resp = await client.get("/api/board", cookies=cookies)
    col_id = resp.json()["columns"][0]["id"]

    resp = await client.put(f"/api/board/columns/{col_id}", json={"title": "Todo"}, cookies=cookies)
    assert resp.status_code == 200

    resp = await client.get("/api/board", cookies=cookies)
    assert resp.json()["columns"][0]["title"] == "Todo"


async def test_rename_column_not_found(client: AsyncClient):
    cookies = await _login(client)
    resp = await client.put("/api/board/columns/col-9999", json={"title": "X"}, cookies=cookies)
    assert resp.status_code == 404


# --- POST /api/board/cards ---

async def test_create_card_requires_auth(client: AsyncClient):
    resp = await client.post("/api/board/cards", json={"column_id": "col-1", "title": "Test"})
    assert resp.status_code == 401


async def test_create_card(client: AsyncClient):
    cookies = await _login(client)
    resp = await client.get("/api/board", cookies=cookies)
    col_id = resp.json()["columns"][0]["id"]

    resp = await client.post(
        "/api/board/cards",
        json={"column_id": col_id, "title": "New task", "details": "Some details"},
        cookies=cookies,
    )
    assert resp.status_code == 200
    card = resp.json()
    assert card["title"] == "New task"
    assert card["details"] == "Some details"
    assert "id" in card

    # Verify it appears in the board
    resp = await client.get("/api/board", cookies=cookies)
    data = resp.json()
    assert card["id"] in data["columns"][0]["cardIds"]
    assert len(data["cards"]) == 9


async def test_create_card_invalid_column(client: AsyncClient):
    cookies = await _login(client)
    resp = await client.post(
        "/api/board/cards",
        json={"column_id": "col-9999", "title": "X"},
        cookies=cookies,
    )
    assert resp.status_code == 404


# --- PUT /api/board/cards/:id ---

async def test_update_card_requires_auth(client: AsyncClient):
    resp = await client.put("/api/board/cards/card-1", json={"title": "X"})
    assert resp.status_code == 401


async def test_update_card(client: AsyncClient):
    cookies = await _login(client)
    resp = await client.get("/api/board", cookies=cookies)
    card_id = resp.json()["columns"][0]["cardIds"][0]

    resp = await client.put(
        f"/api/board/cards/{card_id}",
        json={"title": "Updated", "details": "New details"},
        cookies=cookies,
    )
    assert resp.status_code == 200

    resp = await client.get("/api/board", cookies=cookies)
    assert resp.json()["cards"][card_id]["title"] == "Updated"
    assert resp.json()["cards"][card_id]["details"] == "New details"


async def test_update_card_not_found(client: AsyncClient):
    cookies = await _login(client)
    resp = await client.put(
        "/api/board/cards/card-9999",
        json={"title": "X"},
        cookies=cookies,
    )
    assert resp.status_code == 404


# --- DELETE /api/board/cards/:id ---

async def test_delete_card_requires_auth(client: AsyncClient):
    resp = await client.delete("/api/board/cards/card-1")
    assert resp.status_code == 401


async def test_delete_card(client: AsyncClient):
    cookies = await _login(client)
    resp = await client.get("/api/board", cookies=cookies)
    card_id = resp.json()["columns"][0]["cardIds"][0]

    resp = await client.delete(f"/api/board/cards/{card_id}", cookies=cookies)
    assert resp.status_code == 200

    resp = await client.get("/api/board", cookies=cookies)
    assert card_id not in resp.json()["cards"]
    assert len(resp.json()["cards"]) == 7


async def test_delete_card_not_found(client: AsyncClient):
    cookies = await _login(client)
    resp = await client.delete("/api/board/cards/card-9999", cookies=cookies)
    assert resp.status_code == 404


# --- PUT /api/board/cards/:id/move ---

async def test_move_card_requires_auth(client: AsyncClient):
    resp = await client.put("/api/board/cards/card-1/move", json={"column_id": "col-2", "position": 0})
    assert resp.status_code == 401


async def test_move_card_between_columns(client: AsyncClient):
    cookies = await _login(client)
    resp = await client.get("/api/board", cookies=cookies)
    data = resp.json()
    card_id = data["columns"][0]["cardIds"][0]  # First card in Backlog
    target_col = data["columns"][1]["id"]  # Discovery

    resp = await client.put(
        f"/api/board/cards/{card_id}/move",
        json={"column_id": target_col, "position": 0},
        cookies=cookies,
    )
    assert resp.status_code == 200

    resp = await client.get("/api/board", cookies=cookies)
    data = resp.json()
    # Card should be in Discovery at position 0
    assert data["columns"][1]["cardIds"][0] == card_id
    # Backlog should have one fewer card
    assert len(data["columns"][0]["cardIds"]) == 1


async def test_move_card_within_column(client: AsyncClient):
    cookies = await _login(client)
    resp = await client.get("/api/board", cookies=cookies)
    data = resp.json()
    col_id = data["columns"][0]["id"]  # Backlog
    card_ids = data["columns"][0]["cardIds"]
    first_card = card_ids[0]
    second_card = card_ids[1]

    # Move first card to position 1
    resp = await client.put(
        f"/api/board/cards/{first_card}/move",
        json={"column_id": col_id, "position": 1},
        cookies=cookies,
    )
    assert resp.status_code == 200

    resp = await client.get("/api/board", cookies=cookies)
    new_ids = resp.json()["columns"][0]["cardIds"]
    assert new_ids[0] == second_card
    assert new_ids[1] == first_card


async def test_move_card_not_found(client: AsyncClient):
    cookies = await _login(client)
    resp = await client.put(
        "/api/board/cards/card-9999/move",
        json={"column_id": "col-1", "position": 0},
        cookies=cookies,
    )
    assert resp.status_code == 404
