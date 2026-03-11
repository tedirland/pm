import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.ai import ai_chat, ai_test
from app.database import (
    create_card,
    delete_card,
    ensure_board,
    get_board,
    get_board_by_user,
    move_card,
    update_card,
)
from app.dependencies import get_current_user_id, get_db
from app.models import ChatRequest

router = APIRouter(prefix="/api", tags=["ai"])


def parse_id(prefixed_id: str) -> int:
    """Strip 'col-' or 'card-' prefix and return the integer ID."""
    parts = prefixed_id.split("-", 1)
    return int(parts[1]) if len(parts) == 2 and parts[0] in ("col", "card") else int(prefixed_id)


def _apply_board_updates(conn: sqlite3.Connection, updates: dict, user_id: int, board_id: int) -> bool:
    """Apply AI-requested board changes. Returns True if any changes were made."""
    changed = False

    col_rows = conn.execute(
        "SELECT id, title FROM columns WHERE board_id = ?", (board_id,)
    ).fetchall()
    col_by_title = {r["title"]: r["id"] for r in col_rows}

    for card in updates.get("cards_to_create", []):
        col_id = col_by_title.get(card.get("column_title"))
        if col_id:
            create_card(conn, col_id, card["title"], card.get("details", ""), user_id, card.get("due_date"))
            changed = True

    for card in updates.get("cards_to_update", []):
        cid = parse_id(card["card_id"])
        title = card.get("title")
        details = card.get("details")
        due_date = card.get("due_date", "__UNSET__")
        row = conn.execute("SELECT title, details, due_date FROM cards WHERE id = ?", (cid,)).fetchone()
        if not row:
            continue
        title = title if title is not None else row["title"]
        details = details if details is not None else row["details"]
        resolved_due_date = row["due_date"] if due_date == "__UNSET__" else due_date
        if update_card(conn, cid, title, details, user_id, resolved_due_date):
            changed = True

    for card in updates.get("cards_to_delete", []):
        if delete_card(conn, parse_id(card["card_id"]), user_id):
            changed = True

    for card in updates.get("cards_to_move", []):
        col_id = col_by_title.get(card.get("column_title"))
        if col_id:
            if move_card(conn, parse_id(card["card_id"]), col_id, card["position"], user_id):
                changed = True

    return changed


@router.get("/ai/test")
async def ai_test_endpoint(
    user_id: int = Depends(get_current_user_id),
):
    try:
        result = ai_test()
        return {"response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/chat")
async def ai_chat_endpoint(
    body: ChatRequest,
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    try:
        board_data = get_board_by_user(conn, user_id)
        board_id = board_data["id"]
        history = [{"role": m.role, "content": m.content} for m in body.history]
        result = ai_chat(board_data, body.message, history)

        board_changed = False
        updates = result.get("board_updates")
        if updates:
            board_changed = _apply_board_updates(conn, updates, user_id, board_id)

        return {"message": result["message"], "board_updated": board_changed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/boards/{board_id}/ai/chat")
async def ai_chat_board_endpoint(
    board_id: int,
    body: ChatRequest,
    user_id: int = Depends(get_current_user_id),
    conn: sqlite3.Connection = Depends(get_db),
):
    board_data = get_board(conn, board_id, user_id)
    if not board_data:
        raise HTTPException(status_code=404, detail="Board not found")
    try:
        history = [{"role": m.role, "content": m.content} for m in body.history]
        result = ai_chat(board_data, body.message, history)

        board_changed = False
        updates = result.get("board_updates")
        if updates:
            board_changed = _apply_board_updates(conn, updates, user_id, board_id)

        return {"message": result["message"], "board_updated": board_changed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
