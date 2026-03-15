import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.database import add_column, delete_column, ensure_board, rename_column
from app.dependencies import get_current_user_id, get_db
from app.models import ColumnCreateRequest, ColumnRenameRequest
from app.utils import parse_id

router = APIRouter(prefix="/api", tags=["columns"])


# --- Legacy single-board column endpoints ---

@router.post("/board/columns")
async def board_add_column(
    body: ColumnCreateRequest,
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    board_id = ensure_board(conn, user_id)
    col = add_column(conn, board_id, body.title, user_id)
    if col is None:
        raise HTTPException(status_code=404, detail="Board not found")
    return col


@router.delete("/board/columns/{column_id}")
async def board_delete_column(
    column_id: str,
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    ok = delete_column(conn, parse_id(column_id), user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Column not found")
    return {"ok": True}


@router.put("/board/columns/{column_id}")
async def board_rename_column(
    column_id: str,
    body: ColumnRenameRequest,
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    ok = rename_column(conn, parse_id(column_id), body.title, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Column not found")
    return {"ok": True}


# --- Multi-board column endpoints ---

@router.post("/boards/{board_id}/columns")
async def add_column_on_board(
    board_id: int,
    body: ColumnCreateRequest,
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    _require_board_ownership(conn, board_id, user_id)
    col = add_column(conn, board_id, body.title, user_id)
    if col is None:
        raise HTTPException(status_code=404, detail="Board not found")
    return col


@router.delete("/boards/{board_id}/columns/{column_id}")
async def delete_column_on_board(
    board_id: int,
    column_id: str,
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    _require_board_ownership(conn, board_id, user_id)
    ok = delete_column(conn, parse_id(column_id), user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Column not found")
    return {"ok": True}


@router.put("/boards/{board_id}/columns/{column_id}")
async def rename_column_on_board(
    board_id: int,
    column_id: str,
    body: ColumnRenameRequest,
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    _require_board_ownership(conn, board_id, user_id)
    ok = rename_column(conn, parse_id(column_id), body.title, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Column not found")
    return {"ok": True}


def _require_board_ownership(conn: sqlite3.Connection, board_id: int, user_id: int) -> None:
    """Raise 404 if the board does not exist or is not owned by the user."""
    row = conn.execute(
        "SELECT id FROM boards WHERE id = ? AND user_id = ?",
        (board_id, user_id),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Board not found")
