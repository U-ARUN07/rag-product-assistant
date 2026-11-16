import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.config import get_settings

class ConversationDB:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = get_settings().SQLITE_DB_PATH
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                    content TEXT NOT NULL,
                    sources TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_id ON conversation_history(session_id);
            """)
            conn.commit()

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List[str]] = None
    ) -> int:
        sources_json = json.dumps(sources or [])
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO conversation_history (session_id, role, content, sources, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, role, content, sources_json, datetime.now(timezone.utc).isoformat())
            )
            conn.commit()
            return cursor.lastrowid

    def get_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if limit:
                cursor.execute(
                    """
                    SELECT id, session_id, role, content, sources, created_at
                    FROM conversation_history
                    WHERE session_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (session_id, limit)
                )
                rows = cursor.fetchall()
                rows = list(reversed(rows))
            else:
                cursor.execute(
                    """
                    SELECT id, session_id, role, content, sources, created_at
                    FROM conversation_history
                    WHERE session_id = ?
                    ORDER BY id ASC
                    """,
                    (session_id,)
                )
                rows = cursor.fetchall()

            result = []
            for row in rows:
                result.append({
                    "id": row["id"],
                    "session_id": row["session_id"],
                    "role": row["role"],
                    "content": row["content"],
                    "sources": json.loads(row["sources"]) if row["sources"] else [],
                    "created_at": row["created_at"]
                })
            return result

    def clear_history(self, session_id: str) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversation_history WHERE session_id = ?", (session_id,))
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count

    def get_all_sessions(self) -> List[str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT session_id FROM conversation_history ORDER BY id DESC")
            rows = cursor.fetchall()
            return [row["session_id"] for row in rows]
