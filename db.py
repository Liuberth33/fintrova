import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "fintrova.db"


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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


def save_message(role: str, content: str, news: list[dict]) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO messages (role, content, news) VALUES (?, ?, ?)",
            (role, content, json.dumps(news, ensure_ascii=False)),
        )


def load_messages() -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT role, content, news FROM messages ORDER BY id").fetchall()
    return [{"role": role, "content": content, "news": json.loads(news)} for role, content, news in rows]


def clear_messages() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM messages")


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
