"""Tests for due date support on cards."""
from httpx import AsyncClient


async def test_create_card_with_due_date(authed_client: AsyncClient):
    boards = await authed_client.get("/api/boards")
    board_id = boards.json()[0]["id"]
    board = await authed_client.get(f"/api/boards/{board_id}")
    col_id = board.json()["columns"][0]["id"]

    resp = await authed_client.post(
        "/api/board/cards",
        json={"column_id": col_id, "title": "Due soon", "details": "", "due_date": "2026-04-01"},
    )
    assert resp.status_code == 200
    card = resp.json()
    assert card["due_date"] == "2026-04-01"

    # Verify in board data
    board = await authed_client.get("/api/board")
    assert board.json()["cards"][card["id"]]["due_date"] == "2026-04-01"


async def test_create_card_without_due_date(authed_client: AsyncClient):
    board = await authed_client.get("/api/board")
    col_id = board.json()["columns"][0]["id"]

    resp = await authed_client.post(
        "/api/board/cards",
        json={"column_id": col_id, "title": "No date", "details": ""},
    )
    assert resp.status_code == 200
    assert resp.json()["due_date"] is None


async def test_update_card_with_due_date(authed_client: AsyncClient):
    board = await authed_client.get("/api/board")
    card_id = board.json()["columns"][0]["cardIds"][0]

    resp = await authed_client.put(
        f"/api/board/cards/{card_id}",
        json={"title": "Updated", "details": "d", "due_date": "2026-06-15"},
    )
    assert resp.status_code == 200

    board = await authed_client.get("/api/board")
    assert board.json()["cards"][card_id]["due_date"] == "2026-06-15"


async def test_clear_due_date(authed_client: AsyncClient):
    board = await authed_client.get("/api/board")
    col_id = board.json()["columns"][0]["id"]

    # Create with due date
    resp = await authed_client.post(
        "/api/board/cards",
        json={"column_id": col_id, "title": "Has date", "details": "", "due_date": "2026-05-01"},
    )
    card_id = resp.json()["id"]

    # Clear it
    resp = await authed_client.put(
        f"/api/board/cards/{card_id}",
        json={"title": "Has date", "details": "", "due_date": None},
    )
    assert resp.status_code == 200

    board = await authed_client.get("/api/board")
    assert board.json()["cards"][card_id]["due_date"] is None


async def test_due_date_on_board_scoped_endpoint(authed_client: AsyncClient):
    boards = await authed_client.get("/api/boards")
    board_id = boards.json()[0]["id"]
    board = await authed_client.get(f"/api/boards/{board_id}")
    col_id = board.json()["columns"][0]["id"]

    resp = await authed_client.post(
        f"/api/boards/{board_id}/cards",
        json={"column_id": col_id, "title": "Scoped due", "details": "", "due_date": "2026-12-25"},
    )
    assert resp.status_code == 200
    assert resp.json()["due_date"] == "2026-12-25"
