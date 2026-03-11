from httpx import AsyncClient


# --- POST /api/board/columns ---

async def test_add_column(authed_client: AsyncClient):
    resp = await authed_client.post("/api/board/columns", json={"title": "Deployed"})
    assert resp.status_code == 200
    col = resp.json()
    assert col["title"] == "Deployed"
    assert col["id"].startswith("col-")

    # Verify it appears in the board
    resp = await authed_client.get("/api/board")
    data = resp.json()
    titles = [c["title"] for c in data["columns"]]
    assert "Deployed" in titles
    assert data["columns"][-1]["title"] == "Deployed"


async def test_add_column_requires_auth(client: AsyncClient):
    resp = await client.post("/api/board/columns", json={"title": "Nope"})
    assert resp.status_code == 401


# --- DELETE /api/board/columns/:id ---

async def test_delete_column(authed_client: AsyncClient):
    # Get the first column (has cards)
    resp = await authed_client.get("/api/board")
    data = resp.json()
    col_id = data["columns"][0]["id"]
    card_ids = data["columns"][0]["cardIds"]
    initial_col_count = len(data["columns"])

    resp = await authed_client.delete(f"/api/board/columns/{col_id}")
    assert resp.status_code == 200

    # Verify column and its cards are gone
    resp = await authed_client.get("/api/board")
    data = resp.json()
    assert len(data["columns"]) == initial_col_count - 1
    col_ids = [c["id"] for c in data["columns"]]
    assert col_id not in col_ids
    for card_id in card_ids:
        assert card_id not in data["cards"]


async def test_delete_column_not_found(authed_client: AsyncClient):
    resp = await authed_client.delete("/api/board/columns/col-9999")
    assert resp.status_code == 404


async def test_delete_column_requires_auth(client: AsyncClient):
    resp = await client.delete("/api/board/columns/col-1")
    assert resp.status_code == 401


# --- POST /api/boards/:id/columns ---

async def test_add_column_on_specific_board(authed_client: AsyncClient):
    # Get the board id
    resp = await authed_client.get("/api/board")
    board_id = resp.json()["id"]

    resp = await authed_client.post(f"/api/boards/{board_id}/columns", json={"title": "Archive"})
    assert resp.status_code == 200
    col = resp.json()
    assert col["title"] == "Archive"

    resp = await authed_client.get(f"/api/boards/{board_id}")
    data = resp.json()
    assert data["columns"][-1]["title"] == "Archive"


# --- DELETE /api/boards/:id/columns/:col_id ---

async def test_delete_column_on_specific_board(authed_client: AsyncClient):
    resp = await authed_client.get("/api/board")
    data = resp.json()
    board_id = data["id"]
    col_id = data["columns"][-1]["id"]
    initial_count = len(data["columns"])

    resp = await authed_client.delete(f"/api/boards/{board_id}/columns/{col_id}")
    assert resp.status_code == 200

    resp = await authed_client.get(f"/api/boards/{board_id}")
    assert len(resp.json()["columns"]) == initial_count - 1
