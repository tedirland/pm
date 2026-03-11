import re
import sqlite3

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response

from app.auth import generate_session_token, hash_password, verify_password
from app.database import (
    create_board,
    create_session,
    create_user,
    delete_session,
    get_session_user,
    get_user_by_username,
)
from app.dependencies import get_current_user_id, get_db
from app.models import LoginRequest, RegisterRequest

router = APIRouter(prefix="/api", tags=["auth"])

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,30}$")
MIN_PASSWORD_LENGTH = 8


@router.post("/register")
async def register(
    body: RegisterRequest,
    response: Response,
    conn: sqlite3.Connection = Depends(get_db),
):
    if not USERNAME_RE.match(body.username):
        raise HTTPException(status_code=400, detail="Username must be 3-30 characters, alphanumeric or underscore")
    if len(body.password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(status_code=400, detail=f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
    existing = get_user_by_username(conn, body.username)
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")

    pw_hash = hash_password(body.password)
    user_id = create_user(conn, body.username, pw_hash)
    create_board(conn, user_id, "My Board", seed=True)

    token = generate_session_token()
    create_session(conn, user_id, token)
    response.set_cookie(key="session", value=token, httponly=True, samesite="lax")
    return {"username": body.username}


@router.post("/login")
async def login(
    body: LoginRequest,
    response: Response,
    conn: sqlite3.Connection = Depends(get_db),
):
    user = get_user_by_username(conn, body.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Support legacy users with empty password_hash (pre-migration)
    if user["password_hash"] == "":
        if body.password != "password":
            raise HTTPException(status_code=401, detail="Invalid credentials")
    else:
        if not verify_password(body.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

    token = generate_session_token()
    create_session(conn, user["id"], token)
    response.set_cookie(key="session", value=token, httponly=True, samesite="lax")
    return {"username": user["username"]}


@router.post("/logout")
async def logout(
    response: Response,
    session: str | None = Cookie(default=None),
    conn: sqlite3.Connection = Depends(get_db),
):
    if session:
        delete_session(conn, session)
    response.delete_cookie(key="session")
    return {"ok": True}


@router.get("/me")
async def me(
    session: str | None = Cookie(default=None),
    conn: sqlite3.Connection = Depends(get_db),
):
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = get_session_user(conn, session)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    row = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"username": row["username"]}
