import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.database import create_card, delete_card, ensure_board, move_card, update_card
from app.dependencies import get_current_user_id, get_db
from app.models import CardCreateRequest, CardMoveRequest, CardUpdateRequest

router = APIRouter(prefix="/api", tags=["cards"])


def parse_id(prefixed_id: str) -> int:
    """Strip 'col-' or 'card-' prefix and return the integer ID."""
    parts = prefixed_id.split("-", 1)
    return int(parts[1]) if len(parts) == 2 and parts[0] in ("col", "card") else int(prefixed_id)


# --- Legacy single-board card endpoints ---

@router.post("/board/cards")
async def board_create_card(
    body: CardCreateRequest,
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    card = create_card(conn, parse_id(body.column_id), body.title, body.details, user_id, body.due_date)
    if card is None:
        raise HTTPException(status_code=404, detail="Column not found")
    return card


@router.put("/board/cards/{card_id}")
async def board_update_card(
    card_id: str,
    body: CardUpdateRequest,
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    ok = update_card(conn, parse_id(card_id), body.title, body.details, user_id, body.due_date, body.labels)
    if not ok:
        raise HTTPException(status_code=404, detail="Card not found")
    return {"ok": True}


@router.delete("/board/cards/{card_id}")
async def board_delete_card(
    card_id: str,
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    ok = delete_card(conn, parse_id(card_id), user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Card not found")
    return {"ok": True}


@router.put("/board/cards/{card_id}/move")
async def board_move_card(
    card_id: str,
    body: CardMoveRequest,
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    ok = move_card(conn, parse_id(card_id), parse_id(body.column_id), body.position, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Card or column not found")
    return {"ok": True}


# --- Multi-board card endpoints ---

@router.post("/boards/{board_id}/cards")
async def create_card_on_board(
    board_id: int,
    body: CardCreateRequest,
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    # Verify board ownership
    board = conn.execute(
        "SELECT id FROM boards WHERE id = ? AND user_id = ?",
        (board_id, user_id),
    ).fetchone()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    card = create_card(conn, parse_id(body.column_id), body.title, body.details, user_id, body.due_date)
    if card is None:
        raise HTTPException(status_code=404, detail="Column not found")
    return card


@router.put("/boards/{board_id}/cards/{card_id}")
async def update_card_on_board(
    board_id: int,
    card_id: str,
    body: CardUpdateRequest,
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    board = conn.execute(
        "SELECT id FROM boards WHERE id = ? AND user_id = ?",
        (board_id, user_id),
    ).fetchone()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    ok = update_card(conn, parse_id(card_id), body.title, body.details, user_id, body.due_date, body.labels)
    if not ok:
        raise HTTPException(status_code=404, detail="Card not found")
    return {"ok": True}


@router.delete("/boards/{board_id}/cards/{card_id}")
async def delete_card_on_board(
    board_id: int,
    card_id: str,
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    board = conn.execute(
        "SELECT id FROM boards WHERE id = ? AND user_id = ?",
        (board_id, user_id),
    ).fetchone()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    ok = delete_card(conn, parse_id(card_id), user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Card not found")
    return {"ok": True}


@router.put("/boards/{board_id}/cards/{card_id}/move")
async def move_card_on_board(
    board_id: int,
    card_id: str,
    body: CardMoveRequest,
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    board = conn.execute(
        "SELECT id FROM boards WHERE id = ? AND user_id = ?",
        (board_id, user_id),
    ).fetchone()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    ok = move_card(conn, parse_id(card_id), parse_id(body.column_id), body.position, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Card or column not found")
    return {"ok": True}
