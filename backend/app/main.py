import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Cookie, FastAPI, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

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


def get_authenticated_user_id(session: str | None) -> int | None:
    if session != SESSION_TOKEN:
        return None
    conn = get_connection()
    try:
        user_id = ensure_user(conn, VALID_USERNAME)
        ensure_board(conn, user_id)
        return user_id
    finally:
        conn.close()


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/login")
async def login(body: LoginRequest, response: Response):
    if body.username == VALID_USERNAME and body.password == VALID_PASSWORD:
        response.set_cookie(key="session", value=SESSION_TOKEN, httponly=True, samesite="lax")
        return {"username": body.username}
    return Response(status_code=401, content='{"error":"Invalid credentials"}', media_type="application/json")


@app.post("/api/logout")
async def logout(response: Response):
    response.delete_cookie(key="session")
    return {"ok": True}


@app.get("/api/me")
async def me(session: str | None = Cookie(default=None)):
    if session == SESSION_TOKEN:
        return {"username": VALID_USERNAME}
    return Response(status_code=401, content='{"error":"Not authenticated"}', media_type="application/json")


@app.get("/api/board")
async def board_get(session: str | None = Cookie(default=None)):
    user_id = get_authenticated_user_id(session)
    if user_id is None:
        return Response(status_code=401, content='{"error":"Not authenticated"}', media_type="application/json")
    conn = get_connection()
    try:
        data = get_board(conn, user_id)
        return data
    finally:
        conn.close()


@app.put("/api/board/columns/{column_id}")
async def board_rename_column(column_id: str, body: ColumnRenameRequest, session: str | None = Cookie(default=None)):
    user_id = get_authenticated_user_id(session)
    if user_id is None:
        return Response(status_code=401, content='{"error":"Not authenticated"}', media_type="application/json")
    conn = get_connection()
    try:
        ok = rename_column(conn, int(column_id), body.title, user_id)
        if not ok:
            return Response(status_code=404, content='{"error":"Column not found"}', media_type="application/json")
        return {"ok": True}
    finally:
        conn.close()


@app.post("/api/board/cards")
async def board_create_card(body: CardCreateRequest, session: str | None = Cookie(default=None)):
    user_id = get_authenticated_user_id(session)
    if user_id is None:
        return Response(status_code=401, content='{"error":"Not authenticated"}', media_type="application/json")
    conn = get_connection()
    try:
        card = create_card(conn, int(body.column_id), body.title, body.details, user_id)
        if card is None:
            return Response(status_code=404, content='{"error":"Column not found"}', media_type="application/json")
        return card
    finally:
        conn.close()


@app.put("/api/board/cards/{card_id}")
async def board_update_card(card_id: str, body: CardUpdateRequest, session: str | None = Cookie(default=None)):
    user_id = get_authenticated_user_id(session)
    if user_id is None:
        return Response(status_code=401, content='{"error":"Not authenticated"}', media_type="application/json")
    conn = get_connection()
    try:
        ok = update_card(conn, int(card_id), body.title, body.details, user_id)
        if not ok:
            return Response(status_code=404, content='{"error":"Card not found"}', media_type="application/json")
        return {"ok": True}
    finally:
        conn.close()


@app.delete("/api/board/cards/{card_id}")
async def board_delete_card(card_id: str, session: str | None = Cookie(default=None)):
    user_id = get_authenticated_user_id(session)
    if user_id is None:
        return Response(status_code=401, content='{"error":"Not authenticated"}', media_type="application/json")
    conn = get_connection()
    try:
        ok = delete_card(conn, int(card_id), user_id)
        if not ok:
            return Response(status_code=404, content='{"error":"Card not found"}', media_type="application/json")
        return {"ok": True}
    finally:
        conn.close()


@app.put("/api/board/cards/{card_id}/move")
async def board_move_card(card_id: str, body: CardMoveRequest, session: str | None = Cookie(default=None)):
    user_id = get_authenticated_user_id(session)
    if user_id is None:
        return Response(status_code=401, content='{"error":"Not authenticated"}', media_type="application/json")
    conn = get_connection()
    try:
        ok = move_card(conn, int(card_id), int(body.column_id), body.position, user_id)
        if not ok:
            return Response(status_code=404, content='{"error":"Card or column not found"}', media_type="application/json")
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
