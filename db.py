import json
import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "fintrova.db"

# Nombres "provisionales" que el sistema pone solo mientras la conversación
# no tiene contenido propio todavía — apenas llega el primer mensaje real
# se reemplazan por un extracto de ese mensaje (ver _maybe_auto_name). Si
# el nombre ya no calza con este patrón es porque alguien lo puso a mano
# (o ya se auto-nombró antes), y no se vuelve a tocar.
GENERIC_NAME_PATTERN = re.compile(r"^(Nueva conversación|Conversación anterior|Conversación \d+)$")


def _truncate_topic(text: str, max_len: int = 40) -> str:
    text = " ".join(text.split())
    return text if len(text) <= max_len else text[:max_len].rstrip() + "…"


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
    mete todos los mensajes huérfanos en una conversación nueva, nombrada
    con un extracto del primer mensaje real (no un texto genérico) para no
    perder ni el historial ni el contexto de qué trataba."""
    columns = {row[1] for row in conn.execute("PRAGMA table_info(messages)")}
    if "conversation_id" in columns:
        return
    conn.execute("ALTER TABLE messages ADD COLUMN conversation_id INTEGER REFERENCES conversations(id)")
    orphaned = conn.execute(
        "SELECT role, content FROM messages WHERE conversation_id IS NULL ORDER BY id"
    ).fetchall()
    if not orphaned:
        return
    first_user_msg = next((content for role, content in orphaned if role == "user"), None)
    name = _truncate_topic(first_user_msg) if first_user_msg else "Conversación anterior"
    cursor = conn.execute("INSERT INTO conversations (name) VALUES (?)", (name,))
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
        if role == "user":
            _maybe_auto_name(conn, conversation_id, content)


def _maybe_auto_name(conn: sqlite3.Connection, conversation_id: int, first_message: str) -> None:
    """Si la conversación todavía tiene un nombre provisional (recién
    creada, sin que nadie la haya nombrado a mano), la rebautiza con un
    extracto del mensaje — igual que ChatGPT/Claude nombran solos un chat
    nuevo apenas llega el primer mensaje, en vez de dejarla como "Nueva
    conversación" para siempre. Solo dispara una vez: en cuanto se
    renombra, el nombre ya no calza con GENERIC_NAME_PATTERN y los
    mensajes siguientes no la vuelven a tocar."""
    current_name = conn.execute("SELECT name FROM conversations WHERE id = ?", (conversation_id,)).fetchone()[0]
    if not GENERIC_NAME_PATTERN.match(current_name):
        return
    conn.execute(
        "UPDATE conversations SET name = ? WHERE id = ?",
        (_truncate_topic(first_message), conversation_id),
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
