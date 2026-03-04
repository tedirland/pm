import os
import sqlite3
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


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS boards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
            title TEXT NOT NULL DEFAULT 'My Board'
        );
        CREATE TABLE IF NOT EXISTS columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_id INTEGER NOT NULL REFERENCES boards(id),
            title TEXT NOT NULL,
            position INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            column_id INTEGER NOT NULL REFERENCES columns(id),
            title TEXT NOT NULL,
            details TEXT NOT NULL DEFAULT '',
            position INTEGER NOT NULL
        );
    """)
    conn.commit()


def ensure_user(conn: sqlite3.Connection, username: str) -> int:
    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO users (username) VALUES (?)", (username,))
    conn.commit()
    return cur.lastrowid


def ensure_board(conn: sqlite3.Connection, user_id: int) -> int:
    row = conn.execute("SELECT id FROM boards WHERE user_id = ?", (user_id,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO boards (user_id) VALUES (?)", (user_id,))
    board_id = cur.lastrowid
    # Seed columns
    for position, title in SEED_COLUMNS:
        conn.execute(
            "INSERT INTO columns (board_id, title, position) VALUES (?, ?, ?)",
            (board_id, title, position),
        )
    # Seed cards
    for col_title, position, card_title, details in SEED_CARDS:
        col_row = conn.execute(
            "SELECT id FROM columns WHERE board_id = ? AND title = ?",
            (board_id, col_title),
        ).fetchone()
        conn.execute(
            "INSERT INTO cards (column_id, title, details, position) VALUES (?, ?, ?, ?)",
            (col_row["id"], card_title, details, position),
        )
    conn.commit()
    return board_id


def get_board(conn: sqlite3.Connection, user_id: int) -> dict:
    board_id = ensure_board(conn, user_id)
    cols = conn.execute(
        "SELECT id, title, position FROM columns WHERE board_id = ? ORDER BY position",
        (board_id,),
    ).fetchall()
    columns = []
    cards = {}
    for col in cols:
        col_cards = conn.execute(
            "SELECT id, title, details, position FROM cards WHERE column_id = ? ORDER BY position",
            (col["id"],),
        ).fetchall()
        card_ids = []
        for c in col_cards:
            cid = f"card-{c['id']}"
            card_ids.append(cid)
            cards[cid] = {"id": cid, "title": c["title"], "details": c["details"]}
        columns.append({"id": f"col-{col['id']}", "title": col["title"], "cardIds": card_ids})
    return {"columns": columns, "cards": cards}


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


def create_card(conn: sqlite3.Connection, column_id: int, title: str, details: str, user_id: int) -> dict | None:
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
        "INSERT INTO cards (column_id, title, details, position) VALUES (?, ?, ?, ?)",
        (column_id, title, details, max_pos + 1),
    )
    conn.commit()
    cid = f"card-{cur.lastrowid}"
    return {"id": cid, "title": title, "details": details}


def update_card(conn: sqlite3.Connection, card_id: int, title: str, details: str, user_id: int) -> bool:
    row = conn.execute(
        "SELECT ca.id FROM cards ca JOIN columns co ON ca.column_id = co.id JOIN boards b ON co.board_id = b.id WHERE ca.id = ? AND b.user_id = ?",
        (card_id, user_id),
    ).fetchone()
    if not row:
        return False
    conn.execute("UPDATE cards SET title = ?, details = ? WHERE id = ?", (title, details, card_id))
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
    # Verify target column belongs to same user
    target_col = conn.execute(
        "SELECT c.id FROM columns c JOIN boards b ON c.board_id = b.id WHERE c.id = ? AND b.user_id = ?",
        (target_column_id, user_id),
    ).fetchone()
    if not target_col:
        return False

    old_col = card["column_id"]
    old_pos = card["position"]

    # Remove from old position
    conn.execute(
        "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
        (old_col, old_pos),
    )

    # Make space in target column
    conn.execute(
        "UPDATE cards SET position = position + 1 WHERE column_id = ? AND position >= ?",
        (target_column_id, target_position),
    )

    # Place card
    conn.execute(
        "UPDATE cards SET column_id = ?, position = ? WHERE id = ?",
        (target_column_id, target_position, card_id),
    )
    conn.commit()
    return True
