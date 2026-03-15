import sqlite3

from fastapi import Cookie, Depends, HTTPException

from app.database import get_connection, get_session_user


def get_db() -> sqlite3.Connection:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def get_current_user_id(
    session: str | None = Cookie(default=None),
    conn: sqlite3.Connection = Depends(get_db),
) -> int:
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = get_session_user(conn, session)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id
