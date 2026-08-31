import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "fintrova.db"


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL REFERENCES conversations(id),
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                news TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS backtest_cache (
                cache_key TEXT PRIMARY KEY,
                result TEXT NOT NULL,
                computed_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        _migrate_add_conversation_id(conn)


def _migrate_add_conversation_id(conn: sqlite3.Connection) -> None:
    """Si `messages` ya existía de antes de las sesiones nombradas (una sola
    conversación plana, sin conversation_id), la migra: agrega la columna y
    mete todos los mensajes huérfanos en una conversación nueva, en vez de
    perder el historial existente."""
    columns = {row[1] for row in conn.execute("PRAGMA table_info(messages)")}
    if "conversation_id" in columns:
        return
    conn.execute("ALTER TABLE messages ADD COLUMN conversation_id INTEGER REFERENCES conversations(id)")
    orphaned = conn.execute("SELECT COUNT(*) FROM messages WHERE conversation_id IS NULL").fetchone()[0]
    if orphaned:
        cursor = conn.execute("INSERT INTO conversations (name) VALUES (?)", ("Conversación anterior",))
        conn.execute("UPDATE messages SET conversation_id = ? WHERE conversation_id IS NULL", (cursor.lastrowid,))


def create_conversation(name: str) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("INSERT INTO conversations (name) VALUES (?)", (name,))
        return cursor.lastrowid


def list_conversations() -> list[dict]:
    """Conversaciones ordenadas por actividad más reciente (último mensaje,
    o su propia fecha de creación si todavía no tiene mensajes)."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT c.id, c.name, COALESCE(MAX(m.created_at), c.created_at) AS last_activity
            FROM conversations c
            LEFT JOIN messages m ON m.conversation_id = c.id
            GROUP BY c.id
            ORDER BY last_activity DESC
        """).fetchall()
    return [{"id": id_, "name": name} for id_, name, _ in rows]


def rename_conversation(conversation_id: int, name: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE conversations SET name = ? WHERE id = ?", (name, conversation_id))


def delete_conversation(conversation_id: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))


def save_message(conversation_id: int, role: str, content: str, news: list[dict]) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO messages (conversation_id, role, content, news) VALUES (?, ?, ?, ?)",
            (conversation_id, role, content, json.dumps(news, ensure_ascii=False)),
        )


def load_messages(conversation_id: int) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT role, content, news FROM messages WHERE conversation_id = ? ORDER BY id",
            (conversation_id,),
        ).fetchall()
    return [{"role": role, "content": content, "news": json.loads(news)} for role, content, news in rows]


def get_cached_backtest(cache_key: str, max_age_hours: int = 24) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT result FROM backtest_cache "
            "WHERE cache_key = ? AND computed_at > datetime('now', ?)",
            (cache_key, f"-{max_age_hours} hours"),
        ).fetchone()
    return json.loads(row[0]) if row else None


def save_backtest_cache(cache_key: str, result: dict) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO backtest_cache (cache_key, result, computed_at) VALUES (?, ?, datetime('now')) "
            "ON CONFLICT(cache_key) DO UPDATE SET result = excluded.result, computed_at = excluded.computed_at",
            (cache_key, json.dumps(result, ensure_ascii=False)),
        )
