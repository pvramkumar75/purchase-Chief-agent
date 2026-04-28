from uuid import uuid4
import sqlite3
from typing import Optional

from .db import get_conn, utc_now_iso
from .knowledge import build_search_query


def _row_to_dict(row):
    return dict(row) if row else None


def create_chat(title: Optional[str] = None) -> dict:
    chat_id = str(uuid4())
    timestamp = utc_now_iso()
    chat_title = (title or "New Purchase Session").strip() or "New Purchase Session"

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO chats (id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (chat_id, chat_title, timestamp, timestamp),
        )

    return get_chat(chat_id)


def get_chat(chat_id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM chats
            WHERE id = ?
            """,
            (chat_id,),
        ).fetchone()

    return _row_to_dict(row)


def list_chats() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT c.id, c.title, c.created_at, c.updated_at, COUNT(m.id) AS message_count
            FROM chats c
            LEFT JOIN messages m ON m.chat_id = c.id
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def list_messages(chat_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, chat_id, role, content, created_at
            FROM messages
            WHERE chat_id = ?
            ORDER BY id ASC
            """,
            (chat_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_recent_messages(chat_id: str, limit: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, chat_id, role, content, created_at
            FROM messages
            WHERE chat_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (chat_id, limit),
        ).fetchall()

    history = [dict(row) for row in rows]
    history.reverse()
    return history


def add_message(chat_id: str, role: str, content: str) -> dict:
    timestamp = utc_now_iso()

    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO messages (chat_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (chat_id, role, content, timestamp),
        )

        conn.execute(
            """
            UPDATE chats
            SET updated_at = ?
            WHERE id = ?
            """,
            (timestamp, chat_id),
        )

        if role == "user":
            total_user_messages = conn.execute(
                """
                SELECT COUNT(*) AS c
                FROM messages
                WHERE chat_id = ? AND role = 'user'
                """,
                (chat_id,),
            ).fetchone()["c"]

            if total_user_messages == 1:
                first_line = content.strip().splitlines()[0] if content.strip() else ""
                suggestion = first_line[:64].strip()
                if suggestion:
                    conn.execute(
                        """
                        UPDATE chats
                        SET title = ?
                        WHERE id = ? AND title = 'New Purchase Session'
                        """,
                        (suggestion, chat_id),
                    )

        row = conn.execute(
            """
            SELECT id, chat_id, role, content, created_at
            FROM messages
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

    return dict(row)


def create_document(
    chat_id: str,
    original_name: str,
    stored_path: str,
    mime_type: str,
    char_count: int,
) -> dict:
    doc_id = str(uuid4())
    timestamp = utc_now_iso()

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO documents (id, chat_id, original_name, stored_path, mime_type, char_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (doc_id, chat_id, original_name, stored_path, mime_type, char_count, timestamp),
        )

        row = conn.execute(
            """
            SELECT id, chat_id, original_name, stored_path, mime_type, char_count, created_at
            FROM documents
            WHERE id = ?
            """,
            (doc_id,),
        ).fetchone()

    return dict(row)


def list_documents(chat_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, chat_id, original_name, stored_path, mime_type, char_count, created_at
            FROM documents
            WHERE chat_id = ?
            ORDER BY created_at DESC
            """,
            (chat_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def add_knowledge_chunks(chat_id: str, document_id: str, chunks: list[str]) -> int:
    if not chunks:
        return 0

    with get_conn() as conn:
        for idx, content in enumerate(chunks):
            cursor = conn.execute(
                """
                INSERT INTO knowledge_chunks (chat_id, document_id, chunk_index, content)
                VALUES (?, ?, ?, ?)
                """,
                (chat_id, document_id, idx, content),
            )

            conn.execute(
                """
                INSERT INTO knowledge_chunks_fts (chunk_id, chat_id, document_id, content)
                VALUES (?, ?, ?, ?)
                """,
                (str(cursor.lastrowid), chat_id, document_id, content),
            )

    return len(chunks)


def search_knowledge(chat_id: str, user_query: str, limit: int = 6) -> list[dict]:
    query = build_search_query(user_query)
    if not query:
        return []

    try:
        with get_conn() as conn:
            rows = conn.execute(
                """
                SELECT f.document_id, f.content, d.original_name
                FROM knowledge_chunks_fts f
                JOIN documents d ON d.id = f.document_id
                WHERE f.chat_id = ?
                  AND knowledge_chunks_fts MATCH ?
                LIMIT ?
                """,
                (chat_id, query, limit),
            ).fetchall()
    except sqlite3.OperationalError:
        return []

    return [dict(row) for row in rows]
