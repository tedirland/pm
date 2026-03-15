import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path(os.environ.get("DB_PATH", "/app/data/kanban.db"))

SEED_COLUMNS = [
    (0, "Backlog"),
    (1, "Discovery"),
    (2, "In Progress"),
    (3, "Review"),
    (4, "Done"),
]

SEED_CARDS = [
    ("Backlog", 0, "Align roadmap themes", "Draft quarterly themes with impact statements and metrics."),
    ("Backlog", 1, "Gather customer signals", "Review support tags, sales notes, and churn feedback."),
    ("Discovery", 0, "Prototype analytics view", "Sketch initial dashboard layout and key drill-downs."),
    ("In Progress", 0, "Refine status language", "Standardize column labels and tone across the board."),
    ("In Progress", 1, "Design card layout", "Add hierarchy and spacing for scanning dense lists."),
    ("Review", 0, "QA micro-interactions", "Verify hover, focus, and loading states."),
    ("Done", 0, "Ship marketing page", "Final copy approved and asset pack delivered."),
    ("Done", 1, "Close onboarding sprint", "Document release notes and share internally."),
]

SESSION_EXPIRY_DAYS = 30


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            token TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            expires_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS boards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            title TEXT NOT NULL DEFAULT 'My Board',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_id INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            position INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            column_id INTEGER NOT NULL REFERENCES columns(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            details TEXT NOT NULL DEFAULT '',
            due_date TEXT,
            labels TEXT NOT NULL DEFAULT '[]',
            position INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS labels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_id INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            color TEXT NOT NULL DEFAULT '#888888'
        );
    """)
    conn.commit()


# --- User operations ---

def create_user(conn: sqlite3.Connection, username: str, password_hash: str) -> int:
    cur = conn.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, password_hash),
    )
    conn.commit()
    return cur.lastrowid


def get_user_by_username(conn: sqlite3.Connection, username: str) -> dict | None:
    row = conn.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if not row:
        return None
    return {"id": row["id"], "username": row["username"], "password_hash": row["password_hash"]}


def ensure_user(conn: sqlite3.Connection, username: str) -> int:
    """Get or create a user (legacy support)."""
    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO users (username) VALUES (?)", (username,))
    conn.commit()
    return cur.lastrowid


# --- Session operations ---

def create_session(conn: sqlite3.Connection, user_id: int, token: str) -> None:
    expires = datetime.now(timezone.utc) + timedelta(days=SESSION_EXPIRY_DAYS)
    conn.execute(
        "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, expires.isoformat()),
    )
    conn.commit()


def get_session_user(conn: sqlite3.Connection, token: str) -> int | None:
    """Validate a session token. Returns user_id or None if invalid/expired."""
    row = conn.execute(
        "SELECT user_id, expires_at FROM sessions WHERE token = ?",
        (token,),
    ).fetchone()
    if not row:
        return None
    try:
        expires = datetime.fromisoformat(row["expires_at"])
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < datetime.now(timezone.utc):
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            return None
    except (ValueError, TypeError):
        return None
    return row["user_id"]


def delete_session(conn: sqlite3.Connection, token: str) -> None:
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()


def delete_user_sessions(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    conn.commit()


# --- Board operations ---

def create_board(conn: sqlite3.Connection, user_id: int, title: str = "My Board", seed: bool = True) -> int:
    cur = conn.execute(
        "INSERT INTO boards (user_id, title) VALUES (?, ?)",
        (user_id, title),
    )
    board_id = cur.lastrowid
    if seed:
        _seed_board(conn, board_id)
    conn.commit()
    return board_id


def _seed_board(conn: sqlite3.Connection, board_id: int) -> None:
    for position, title in SEED_COLUMNS:
        conn.execute(
            "INSERT INTO columns (board_id, title, position) VALUES (?, ?, ?)",
            (board_id, title, position),
        )
    for col_title, position, card_title, details in SEED_CARDS:
        col_row = conn.execute(
            "SELECT id FROM columns WHERE board_id = ? AND title = ?",
            (board_id, col_title),
        ).fetchone()
        conn.execute(
            "INSERT INTO cards (column_id, title, details, position) VALUES (?, ?, ?, ?)",
            (col_row["id"], card_title, details, position),
        )


def ensure_board(conn: sqlite3.Connection, user_id: int) -> int:
    """Get or create a board (legacy support)."""
    row = conn.execute("SELECT id FROM boards WHERE user_id = ?", (user_id,)).fetchone()
    if row:
        return row["id"]
    return create_board(conn, user_id)


def get_boards(conn: sqlite3.Connection, user_id: int) -> list[dict]:
    rows = conn.execute(
        """SELECT b.id, b.title, b.created_at,
                  (SELECT COUNT(*) FROM columns c WHERE c.board_id = b.id) as column_count,
                  (SELECT COUNT(*) FROM cards ca JOIN columns c ON ca.column_id = c.id WHERE c.board_id = b.id) as card_count
           FROM boards b WHERE b.user_id = ? ORDER BY b.created_at""",
        (user_id,),
    ).fetchall()
    return [
        {"id": r["id"], "title": r["title"], "created_at": r["created_at"],
         "column_count": r["column_count"], "card_count": r["card_count"]}
        for r in rows
    ]


def get_board(conn: sqlite3.Connection, board_id: int, user_id: int) -> dict | None:
    board = conn.execute(
        "SELECT id, title FROM boards WHERE id = ? AND user_id = ?",
        (board_id, user_id),
    ).fetchone()
    if not board:
        return None
    return _load_board_data(conn, board_id)


def get_board_by_user(conn: sqlite3.Connection, user_id: int) -> dict:
    """Get the first board for a user (legacy compat)."""
    board_id = ensure_board(conn, user_id)
    return _load_board_data(conn, board_id)


def _load_board_data(conn: sqlite3.Connection, board_id: int) -> dict:
    board_row = conn.execute("SELECT id, title FROM boards WHERE id = ?", (board_id,)).fetchone()
    cols = conn.execute(
        "SELECT id, title, position FROM columns WHERE board_id = ? ORDER BY position",
        (board_id,),
    ).fetchall()
    columns = []
    cards = {}
    for col in cols:
        col_cards = conn.execute(
            "SELECT id, title, details, due_date, labels, position FROM cards WHERE column_id = ? ORDER BY position",
            (col["id"],),
        ).fetchall()
        card_ids = []
        for c in col_cards:
            cid = f"card-{c['id']}"
            card_ids.append(cid)
            cards[cid] = {
                "id": cid,
                "title": c["title"],
                "details": c["details"],
                "due_date": c["due_date"],
                "labels": c["labels"],
            }
        columns.append({"id": f"col-{col['id']}", "title": col["title"], "cardIds": card_ids})
    return {"id": board_id, "title": board_row["title"], "columns": columns, "cards": cards}


def update_board(conn: sqlite3.Connection, board_id: int, title: str, user_id: int) -> bool:
    row = conn.execute(
        "SELECT id FROM boards WHERE id = ? AND user_id = ?",
        (board_id, user_id),
    ).fetchone()
    if not row:
        return False
    conn.execute("UPDATE boards SET title = ? WHERE id = ?", (title, board_id))
    conn.commit()
    return True


def delete_board(conn: sqlite3.Connection, board_id: int, user_id: int) -> bool:
    row = conn.execute(
        "SELECT id FROM boards WHERE id = ? AND user_id = ?",
        (board_id, user_id),
    ).fetchone()
    if not row:
        return False
    conn.execute("DELETE FROM boards WHERE id = ?", (board_id,))
    conn.commit()
    return True


# --- Column operations ---

def add_column(conn: sqlite3.Connection, board_id: int, title: str, user_id: int) -> dict | None:
    row = conn.execute(
        "SELECT id FROM boards WHERE id = ? AND user_id = ?",
        (board_id, user_id),
    ).fetchone()
    if not row:
        return None
    max_pos = conn.execute(
        "SELECT COALESCE(MAX(position), -1) as mp FROM columns WHERE board_id = ?",
        (board_id,),
    ).fetchone()["mp"]
    cur = conn.execute(
        "INSERT INTO columns (board_id, title, position) VALUES (?, ?, ?)",
        (board_id, title, max_pos + 1),
    )
    conn.commit()
    return {"id": f"col-{cur.lastrowid}", "title": title}


def delete_column(conn: sqlite3.Connection, column_id: int, user_id: int) -> bool:
    row = conn.execute(
        "SELECT c.id, c.board_id, c.position FROM columns c JOIN boards b ON c.board_id = b.id WHERE c.id = ? AND b.user_id = ?",
        (column_id, user_id),
    ).fetchone()
    if not row:
        return False
    board_id = row["board_id"]
    position = row["position"]
    conn.execute("DELETE FROM columns WHERE id = ?", (column_id,))
    conn.execute(
        "UPDATE columns SET position = position - 1 WHERE board_id = ? AND position > ?",
        (board_id, position),
    )
    conn.commit()
    return True


def rename_column(conn: sqlite3.Connection, column_id: int, title: str, user_id: int) -> bool:
    row = conn.execute(
        "SELECT c.id FROM columns c JOIN boards b ON c.board_id = b.id WHERE c.id = ? AND b.user_id = ?",
        (column_id, user_id),
    ).fetchone()
    if not row:
        return False
    conn.execute("UPDATE columns SET title = ? WHERE id = ?", (title, column_id))
    conn.commit()
    return True


# --- Card operations ---

def create_card(conn: sqlite3.Connection, column_id: int, title: str, details: str, user_id: int, due_date: str | None = None) -> dict | None:
    row = conn.execute(
        "SELECT c.id FROM columns c JOIN boards b ON c.board_id = b.id WHERE c.id = ? AND b.user_id = ?",
        (column_id, user_id),
    ).fetchone()
    if not row:
        return None
    max_pos = conn.execute(
        "SELECT COALESCE(MAX(position), -1) as mp FROM cards WHERE column_id = ?",
        (column_id,),
    ).fetchone()["mp"]
    cur = conn.execute(
        "INSERT INTO cards (column_id, title, details, due_date, position) VALUES (?, ?, ?, ?, ?)",
        (column_id, title, details, due_date, max_pos + 1),
    )
    conn.commit()
    cid = f"card-{cur.lastrowid}"
    return {"id": cid, "title": title, "details": details, "due_date": due_date}


def update_card(conn: sqlite3.Connection, card_id: int, title: str, details: str, user_id: int, due_date: str | None = None, labels: str | None = None) -> bool:
    row = conn.execute(
        "SELECT ca.id FROM cards ca JOIN columns co ON ca.column_id = co.id JOIN boards b ON co.board_id = b.id WHERE ca.id = ? AND b.user_id = ?",
        (card_id, user_id),
    ).fetchone()
    if not row:
        return False
    conn.execute("UPDATE cards SET title = ?, details = ?, due_date = ?, labels = ? WHERE id = ?", (title, details, due_date, labels or "", card_id))
    conn.commit()
    return True


def delete_card(conn: sqlite3.Connection, card_id: int, user_id: int) -> bool:
    row = conn.execute(
        "SELECT ca.id, ca.column_id, ca.position FROM cards ca JOIN columns co ON ca.column_id = co.id JOIN boards b ON co.board_id = b.id WHERE ca.id = ? AND b.user_id = ?",
        (card_id, user_id),
    ).fetchone()
    if not row:
        return False
    conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    conn.execute(
        "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
        (row["column_id"], row["position"]),
    )
    conn.commit()
    return True


def move_card(conn: sqlite3.Connection, card_id: int, target_column_id: int, target_position: int, user_id: int) -> bool:
    card = conn.execute(
        "SELECT ca.id, ca.column_id, ca.position FROM cards ca JOIN columns co ON ca.column_id = co.id JOIN boards b ON co.board_id = b.id WHERE ca.id = ? AND b.user_id = ?",
        (card_id, user_id),
    ).fetchone()
    if not card:
        return False
    target_col = conn.execute(
        "SELECT c.id FROM columns c JOIN boards b ON c.board_id = b.id WHERE c.id = ? AND b.user_id = ?",
        (target_column_id, user_id),
    ).fetchone()
    if not target_col:
        return False

    old_col = card["column_id"]
    old_pos = card["position"]

    conn.execute(
        "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
        (old_col, old_pos),
    )
    conn.execute(
        "UPDATE cards SET position = position + 1 WHERE column_id = ? AND position >= ?",
        (target_column_id, target_position),
    )
    conn.execute(
        "UPDATE cards SET column_id = ?, position = ? WHERE id = ?",
        (target_column_id, target_position, card_id),
    )
    conn.commit()
    return True


# --- Label operations ---

def create_label(conn: sqlite3.Connection, board_id: int, name: str, color: str, user_id: int) -> dict | None:
    row = conn.execute(
        "SELECT id FROM boards WHERE id = ? AND user_id = ?",
        (board_id, user_id),
    ).fetchone()
    if not row:
        return None
    cur = conn.execute(
        "INSERT INTO labels (board_id, name, color) VALUES (?, ?, ?)",
        (board_id, name, color),
    )
    conn.commit()
    return {"id": cur.lastrowid, "name": name, "color": color}


def get_labels(conn: sqlite3.Connection, board_id: int, user_id: int) -> list[dict] | None:
    row = conn.execute(
        "SELECT id FROM boards WHERE id = ? AND user_id = ?",
        (board_id, user_id),
    ).fetchone()
    if not row:
        return None
    rows = conn.execute(
        "SELECT id, name, color FROM labels WHERE board_id = ?",
        (board_id,),
    ).fetchall()
    return [{"id": r["id"], "name": r["name"], "color": r["color"]} for r in rows]


def delete_label(conn: sqlite3.Connection, label_id: int, user_id: int) -> bool:
    row = conn.execute(
        "SELECT l.id FROM labels l JOIN boards b ON l.board_id = b.id WHERE l.id = ? AND b.user_id = ?",
        (label_id, user_id),
    ).fetchone()
    if not row:
        return False
    conn.execute("DELETE FROM labels WHERE id = ?", (label_id,))
    conn.commit()
    return True
