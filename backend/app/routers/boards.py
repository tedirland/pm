import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.database import (
    create_board,
    delete_board,
    get_board,
    get_board_by_user,
    get_boards,
    get_labels,
    update_board,
)
from app.dependencies import get_current_user_id, get_db
from app.models import BoardCreateRequest, BoardUpdateRequest

router = APIRouter(prefix="/api", tags=["boards"])


# --- Multi-board endpoints ---

@router.get("/boards")
async def list_boards(
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    return get_boards(conn, user_id)


@router.post("/boards")
async def create_board_endpoint(
    body: BoardCreateRequest,
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    board_id = create_board(conn, user_id, body.title, seed=True)
    board = get_board(conn, board_id, user_id)
    return board


@router.get("/boards/{board_id}")
async def get_board_endpoint(
    board_id: int,
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    board = get_board(conn, board_id, user_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return board


@router.put("/boards/{board_id}")
async def update_board_endpoint(
    board_id: int,
    body: BoardUpdateRequest,
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    ok = update_board(conn, board_id, body.title, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Board not found")
    return {"ok": True}


@router.delete("/boards/{board_id}")
async def delete_board_endpoint(
    board_id: int,
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    ok = delete_board(conn, board_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Board not found")
    return {"ok": True}


@router.get("/boards/{board_id}/labels")
async def get_board_labels(
    board_id: int,
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    labels = get_labels(conn, board_id, user_id)
    if labels is None:
        raise HTTPException(status_code=404, detail="Board not found")
    return labels


# --- Legacy single-board endpoints (backward compatibility) ---

@router.get("/board")
async def board_get_legacy(
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    return get_board_by_user(conn, user_id)
