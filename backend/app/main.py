import json
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Cookie, FastAPI, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.ai import ai_chat, ai_test
from app.database import (
    create_card,
    delete_card,
    ensure_board,
    ensure_user,
    get_board,
    get_connection,
    init_db,
    move_card,
    rename_column,
    update_card,
)

STATIC_DIR = Path(os.environ.get("STATIC_DIR", str(Path(__file__).resolve().parent.parent.parent / "static")))

VALID_USERNAME = "user"
VALID_PASSWORD = "password"
SESSION_TOKEN = "valid-session"


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = get_connection()
    init_db(conn)
    conn.close()
    yield

app = FastAPI(title="Kanban Studio API", lifespan=lifespan)


class LoginRequest(BaseModel):
    username: str
    password: str


class CardCreateRequest(BaseModel):
    column_id: str
    title: str
    details: str = ""


class CardUpdateRequest(BaseModel):
    title: str
    details: str = ""


class CardMoveRequest(BaseModel):
    column_id: str
    position: int


class ColumnRenameRequest(BaseModel):
    title: str


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


def _error_response(status_code: int, message: str) -> Response:
    """Return a JSON error response with proper escaping."""
    return Response(
        status_code=status_code,
        content=json.dumps({"error": message}),
        media_type="application/json",
    )


def get_authenticated_user_id(session: str | None, conn: sqlite3.Connection | None = None) -> int | None:
    """Validate session and return user_id. If conn is provided, uses it; otherwise opens a new connection."""
    if session != SESSION_TOKEN:
        return None
    should_close = conn is None
    if conn is None:
        conn = get_connection()
    try:
        user_id = ensure_user(conn, VALID_USERNAME)
        ensure_board(conn, user_id)
        return user_id
    finally:
        if should_close:
            conn.close()


def parse_id(prefixed_id: str) -> int:
    """Strip 'col-' or 'card-' prefix and return the integer ID."""
    parts = prefixed_id.split("-", 1)
    return int(parts[1]) if len(parts) == 2 and parts[0] in ("col", "card") else int(prefixed_id)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/ai/test")
async def ai_test_endpoint(session: str | None = Cookie(default=None)):
    user_id = get_authenticated_user_id(session)
    if user_id is None:
        return _error_response(401, "Not authenticated")
    try:
        result = ai_test()
        return {"response": result}
    except Exception as e:
        return _error_response(500, str(e))


@app.post("/api/ai/chat")
async def ai_chat_endpoint(body: ChatRequest, session: str | None = Cookie(default=None)):
    conn = get_connection()
    try:
        user_id = get_authenticated_user_id(session, conn)
        if user_id is None:
            return _error_response(401, "Not authenticated")
        board_data = get_board(conn, user_id)
        history = [{"role": m.role, "content": m.content} for m in body.history]
        result = ai_chat(board_data, body.message, history)

        board_changed = False
        updates = result.get("board_updates")
        if updates:
            board_changed = _apply_board_updates(conn, updates, user_id)

        return {"message": result["message"], "board_updated": board_changed}
    except Exception as e:
        return _error_response(500, str(e))
    finally:
        conn.close()


def _apply_board_updates(conn, updates: dict, user_id: int) -> bool:
    """Apply AI-requested board changes. Returns True if any changes were made."""
    changed = False

    # Resolve column titles to IDs
    board_id = ensure_board(conn, user_id)
    col_rows = conn.execute(
        "SELECT id, title FROM columns WHERE board_id = ?", (board_id,)
    ).fetchall()
    col_by_title = {r["title"]: r["id"] for r in col_rows}

    for card in updates.get("cards_to_create", []):
        col_id = col_by_title.get(card.get("column_title"))
        if col_id:
            create_card(conn, col_id, card["title"], card.get("details", ""), user_id)
            changed = True

    for card in updates.get("cards_to_update", []):
        cid = parse_id(card["card_id"])
        title = card.get("title")
        details = card.get("details")
        # Fetch current values for fields not provided
        if title is None or details is None:
            row = conn.execute("SELECT title, details FROM cards WHERE id = ?", (cid,)).fetchone()
            if row:
                title = title if title is not None else row["title"]
                details = details if details is not None else row["details"]
            else:
                continue
        if update_card(conn, cid, title, details, user_id):
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


@app.post("/api/login")
async def login(body: LoginRequest, response: Response):
    if body.username == VALID_USERNAME and body.password == VALID_PASSWORD:
        response.set_cookie(key="session", value=SESSION_TOKEN, httponly=True, samesite="lax")
        return {"username": body.username}
    return _error_response(401, "Invalid credentials")


@app.post("/api/logout")
async def logout(response: Response):
    response.delete_cookie(key="session")
    return {"ok": True}


@app.get("/api/me")
async def me(session: str | None = Cookie(default=None)):
    if session == SESSION_TOKEN:
        return {"username": VALID_USERNAME}
    return _error_response(401, "Not authenticated")


@app.get("/api/board")
async def board_get(session: str | None = Cookie(default=None)):
    conn = get_connection()
    try:
        user_id = get_authenticated_user_id(session, conn)
        if user_id is None:
            return _error_response(401, "Not authenticated")
        data = get_board(conn, user_id)
        return data
    finally:
        conn.close()


@app.put("/api/board/columns/{column_id}")
async def board_rename_column(column_id: str, body: ColumnRenameRequest, session: str | None = Cookie(default=None)):
    conn = get_connection()
    try:
        user_id = get_authenticated_user_id(session, conn)
        if user_id is None:
            return _error_response(401, "Not authenticated")
        ok = rename_column(conn, parse_id(column_id), body.title, user_id)
        if not ok:
            return _error_response(404, "Column not found")
        return {"ok": True}
    finally:
        conn.close()


@app.post("/api/board/cards")
async def board_create_card(body: CardCreateRequest, session: str | None = Cookie(default=None)):
    conn = get_connection()
    try:
        user_id = get_authenticated_user_id(session, conn)
        if user_id is None:
            return _error_response(401, "Not authenticated")
        card = create_card(conn, parse_id(body.column_id), body.title, body.details, user_id)
        if card is None:
            return _error_response(404, "Column not found")
        return card
    finally:
        conn.close()


@app.put("/api/board/cards/{card_id}")
async def board_update_card(card_id: str, body: CardUpdateRequest, session: str | None = Cookie(default=None)):
    conn = get_connection()
    try:
        user_id = get_authenticated_user_id(session, conn)
        if user_id is None:
            return _error_response(401, "Not authenticated")
        ok = update_card(conn, parse_id(card_id), body.title, body.details, user_id)
        if not ok:
            return _error_response(404, "Card not found")
        return {"ok": True}
    finally:
        conn.close()


@app.delete("/api/board/cards/{card_id}")
async def board_delete_card(card_id: str, session: str | None = Cookie(default=None)):
    conn = get_connection()
    try:
        user_id = get_authenticated_user_id(session, conn)
        if user_id is None:
            return _error_response(401, "Not authenticated")
        ok = delete_card(conn, parse_id(card_id), user_id)
        if not ok:
            return _error_response(404, "Card not found")
        return {"ok": True}
    finally:
        conn.close()


@app.put("/api/board/cards/{card_id}/move")
async def board_move_card(card_id: str, body: CardMoveRequest, session: str | None = Cookie(default=None)):
    conn = get_connection()
    try:
        user_id = get_authenticated_user_id(session, conn)
        if user_id is None:
            return _error_response(401, "Not authenticated")
        ok = move_card(conn, parse_id(card_id), parse_id(body.column_id), body.position, user_id)
        if not ok:
            return _error_response(404, "Card or column not found")
        return {"ok": True}
    finally:
        conn.close()


if STATIC_DIR.is_dir():
    @app.get("/")
    async def index():
        return FileResponse(STATIC_DIR / "index.html")

    app.mount("/_next", StaticFiles(directory=STATIC_DIR / "_next"), name="next-assets")
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
else:
    @app.get("/", response_class=HTMLResponse)
    async def index():
        return """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Kanban Studio</title></head>
<body>
<h1>Hello World</h1>
<p>Kanban Studio backend is running. No frontend build found.</p>
</body>
</html>"""
