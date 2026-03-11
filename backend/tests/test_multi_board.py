"""Tests for multi-board support."""
from httpx import AsyncClient


async def test_list_boards(authed_client: AsyncClient):
    resp = await authed_client.get("/api/boards")
    assert resp.status_code == 200
    boards = resp.json()
    assert len(boards) == 1
    assert boards[0]["title"] == "My Board"


async def test_create_board(authed_client: AsyncClient):
    resp = await authed_client.post("/api/boards", json={"title": "Sprint Board"})
    assert resp.status_code == 200
    board = resp.json()
    assert board["title"] == "Sprint Board"
    assert len(board["columns"]) == 5
    assert len(board["cards"]) == 8


async def test_multiple_boards(authed_client: AsyncClient):
    await authed_client.post("/api/boards", json={"title": "Board 2"})
    await authed_client.post("/api/boards", json={"title": "Board 3"})
    resp = await authed_client.get("/api/boards")
    assert len(resp.json()) == 3


async def test_get_specific_board(authed_client: AsyncClient):
    boards_resp = await authed_client.get("/api/boards")
    board_id = boards_resp.json()[0]["id"]
    resp = await authed_client.get(f"/api/boards/{board_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "My Board"
    assert len(resp.json()["columns"]) == 5


async def test_get_nonexistent_board(authed_client: AsyncClient):
    resp = await authed_client.get("/api/boards/9999")
    assert resp.status_code == 404


async def test_update_board_title(authed_client: AsyncClient):
    boards = await authed_client.get("/api/boards")
    board_id = boards.json()[0]["id"]
    resp = await authed_client.put(f"/api/boards/{board_id}", json={"title": "Renamed"})
    assert resp.status_code == 200
    board = await authed_client.get(f"/api/boards/{board_id}")
    assert board.json()["title"] == "Renamed"


async def test_delete_board(authed_client: AsyncClient):
    # Create a second board to delete
    create_resp = await authed_client.post("/api/boards", json={"title": "To Delete"})
    board_id = create_resp.json()["id"]
    resp = await authed_client.delete(f"/api/boards/{board_id}")
    assert resp.status_code == 200
    # Should be gone
    get_resp = await authed_client.get(f"/api/boards/{board_id}")
    assert get_resp.status_code == 404


async def test_delete_nonexistent_board(authed_client: AsyncClient):
    resp = await authed_client.delete("/api/boards/9999")
    assert resp.status_code == 404


async def test_board_isolation_between_users(client: AsyncClient):
    """User A cannot access User B's boards."""
    # Register user A
    reg_a = await client.post("/api/register", json={"username": "user_a", "password": "password123"})
    cookies_a = dict(reg_a.cookies)
    boards_a = await client.get("/api/boards", cookies=cookies_a)
    board_a_id = boards_a.json()[0]["id"]

    # Register user B
    reg_b = await client.post("/api/register", json={"username": "user_b", "password": "password123"})
    cookies_b = dict(reg_b.cookies)

    # User B cannot access User A's board
    resp = await client.get(f"/api/boards/{board_a_id}", cookies=cookies_b)
    assert resp.status_code == 404


async def test_cards_on_specific_board(authed_client: AsyncClient):
    boards = await authed_client.get("/api/boards")
    board_id = boards.json()[0]["id"]
    board = await authed_client.get(f"/api/boards/{board_id}")
    col_id = board.json()["columns"][0]["id"]

    # Create card on specific board
    resp = await authed_client.post(
        f"/api/boards/{board_id}/cards",
        json={"column_id": col_id, "title": "Board-scoped card", "details": "test"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Board-scoped card"

    # Verify it's on the board
    board = await authed_client.get(f"/api/boards/{board_id}")
    assert len(board.json()["cards"]) == 9


async def test_rename_column_on_specific_board(authed_client: AsyncClient):
    boards = await authed_client.get("/api/boards")
    board_id = boards.json()[0]["id"]
    board = await authed_client.get(f"/api/boards/{board_id}")
    col_id = board.json()["columns"][0]["id"]

    resp = await authed_client.put(
        f"/api/boards/{board_id}/columns/{col_id}",
        json={"title": "Renamed Col"},
    )
    assert resp.status_code == 200

    board = await authed_client.get(f"/api/boards/{board_id}")
    assert board.json()["columns"][0]["title"] == "Renamed Col"


async def test_move_card_on_specific_board(authed_client: AsyncClient):
    boards = await authed_client.get("/api/boards")
    board_id = boards.json()[0]["id"]
    board = await authed_client.get(f"/api/boards/{board_id}")
    data = board.json()
    card_id = data["columns"][0]["cardIds"][0]
    target_col = data["columns"][1]["id"]

    resp = await authed_client.put(
        f"/api/boards/{board_id}/cards/{card_id}/move",
        json={"column_id": target_col, "position": 0},
    )
    assert resp.status_code == 200


async def test_delete_card_on_specific_board(authed_client: AsyncClient):
    boards = await authed_client.get("/api/boards")
    board_id = boards.json()[0]["id"]
    board = await authed_client.get(f"/api/boards/{board_id}")
    card_id = board.json()["columns"][0]["cardIds"][0]

    resp = await authed_client.delete(f"/api/boards/{board_id}/cards/{card_id}")
    assert resp.status_code == 200

    board = await authed_client.get(f"/api/boards/{board_id}")
    assert card_id not in board.json()["cards"]


async def test_boards_require_auth(client: AsyncClient):
    resp = await client.get("/api/boards")
    assert resp.status_code == 401


async def test_legacy_board_endpoint_still_works(authed_client: AsyncClient):
    """The old /api/board endpoint returns the first board."""
    resp = await authed_client.get("/api/board")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["columns"]) == 5
    assert len(data["cards"]) == 8
