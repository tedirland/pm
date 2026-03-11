"""Tests for card labels support."""
from httpx import AsyncClient


async def test_update_card_with_labels(authed_client: AsyncClient):
    board = await authed_client.get("/api/board")
    card_id = board.json()["columns"][0]["cardIds"][0]

    resp = await authed_client.put(
        f"/api/board/cards/{card_id}",
        json={"title": "Labeled", "details": "d", "labels": "bug,feature"},
    )
    assert resp.status_code == 200

    board = await authed_client.get("/api/board")
    assert board.json()["cards"][card_id]["labels"] == "bug,feature"


async def test_update_card_clear_labels(authed_client: AsyncClient):
    board = await authed_client.get("/api/board")
    card_id = board.json()["columns"][0]["cardIds"][0]

    # Set labels
    await authed_client.put(
        f"/api/board/cards/{card_id}",
        json={"title": "Labeled", "details": "d", "labels": "bug"},
    )

    # Clear labels
    resp = await authed_client.put(
        f"/api/board/cards/{card_id}",
        json={"title": "Labeled", "details": "d", "labels": None},
    )
    assert resp.status_code == 200

    board = await authed_client.get("/api/board")
    assert board.json()["cards"][card_id]["labels"] == ""


async def test_labels_on_board_scoped_endpoint(authed_client: AsyncClient):
    boards = await authed_client.get("/api/boards")
    board_id = boards.json()[0]["id"]
    board = await authed_client.get(f"/api/boards/{board_id}")
    card_id = board.json()["columns"][0]["cardIds"][0]

    resp = await authed_client.put(
        f"/api/boards/{board_id}/cards/{card_id}",
        json={"title": "Scoped labels", "details": "", "labels": "urgent,design"},
    )
    assert resp.status_code == 200

    board = await authed_client.get(f"/api/boards/{board_id}")
    assert board.json()["cards"][card_id]["labels"] == "urgent,design"


async def test_board_title_update(authed_client: AsyncClient):
    boards = await authed_client.get("/api/boards")
    board_id = boards.json()[0]["id"]

    resp = await authed_client.put(
        f"/api/boards/{board_id}",
        json={"title": "Renamed Board"},
    )
    assert resp.status_code == 200

    board = await authed_client.get(f"/api/boards/{board_id}")
    assert board.json()["title"] == "Renamed Board"
