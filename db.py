import sqlite3
from datetime import datetime, timezone

DB_PATH = "bot.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                list_key TEXT NOT NULL,
                content TEXT NOT NULL,
                description TEXT,
                assignee TEXT,
                creator_id INTEGER NOT NULL,
                creator_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                done_at TEXT,
                done_by TEXT
            )
            """
        )
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(tasks)")}
        if "description" not in columns:
            conn.execute("ALTER TABLE tasks ADD COLUMN description TEXT")


def add_task(
    chat_id: int,
    list_key: str,
    content: str,
    description: str | None,
    assignee: str | None,
    creator_id: int,
    creator_name: str,
) -> int:
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO tasks
                (chat_id, list_key, content, description, assignee,
                 creator_id, creator_name, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                chat_id, list_key, content, description, assignee,
                creator_id, creator_name, _now(),
            ),
        )
        return int(cur.lastrowid)


def get_tasks(chat_id: int, list_key: str) -> list[sqlite3.Row]:
    with _connect() as conn:
        cur = conn.execute(
            "SELECT * FROM tasks WHERE chat_id = ? AND list_key = ? ORDER BY id ASC",
            (chat_id, list_key),
        )
        return cur.fetchall()


def get_task(task_id: int) -> sqlite3.Row | None:
    with _connect() as conn:
        cur = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return cur.fetchone()


def mark_done(task_id: int, done_by: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE tasks SET status = 'done', done_at = ?, done_by = ? WHERE id = ?",
            (_now(), done_by, task_id),
        )


def clear_done(chat_id: int) -> int:
    with _connect() as conn:
        cur = conn.execute(
            "DELETE FROM tasks WHERE chat_id = ? AND status = 'done'", (chat_id,)
        )
        return cur.rowcount
