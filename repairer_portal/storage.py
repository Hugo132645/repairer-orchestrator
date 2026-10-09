from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any, Literal

AccountRole = Literal["administrator", "repairer"]

PROTOTYPE_ACCOUNTS = (
    ("demo.repairer", "Synthetic123!", "repairer", "Demo repairer"),
    ("demo.admin", "AdminSynthetic123!", "administrator", "Demo administrator"),
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _password_hash(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 210_000)


class PortalRepository:
    """SQLite-backed prototype identity and conversation repository."""

    def __init__(self, database: str | Path) -> None:
        if database != ":memory:":
            path = Path(database)
            path.parent.mkdir(parents=True, exist_ok=True)
            database = path
        self._connection = sqlite3.connect(database, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = RLock()
        self._create_schema()
        self._seed_accounts()

    def _execute(self, sql: str, parameters: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        return self._connection.execute(sql, parameters)

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def _create_schema(self) -> None:
        with self._lock, self._connection:
            self._connection.executescript(
                """
                PRAGMA foreign_keys = ON;
                CREATE TABLE IF NOT EXISTS accounts (
                    username TEXT PRIMARY KEY,
                    password_salt BLOB NOT NULL,
                    password_hash BLOB NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('administrator', 'repairer')),
                    display_name TEXT NOT NULL,
                    language TEXT NOT NULL DEFAULT 'en'
                );
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL REFERENCES accounts(username),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS conversations_user_updated
                    ON conversations(username, updated_at DESC);
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id),
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                    text TEXT NOT NULL,
                    metadata_json TEXT,
                    occurred_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS service_history (
                    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL REFERENCES accounts(username),
                    conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id),
                    payload_json TEXT NOT NULL,
                    occurred_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS repair_orders (
                    repair_order_id TEXT NOT NULL,
                    username TEXT NOT NULL REFERENCES accounts(username),
                    conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id),
                    payload_json TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    PRIMARY KEY (username, repair_order_id)
                );
                """
            )
            self._migrate_repair_order_identity()
            self._migrate_repair_order_references()

    def _migrate_repair_order_identity(self) -> None:
        columns = self._execute("PRAGMA table_info(repair_orders)").fetchall()
        primary_key_columns = [
            row["name"] for row in sorted(columns, key=lambda row: row["pk"]) if row["pk"] > 0
        ]
        if primary_key_columns == ["username", "repair_order_id"]:
            return
        self._connection.executescript(
            """
            ALTER TABLE repair_orders RENAME TO repair_orders_legacy;
            CREATE TABLE repair_orders (
                repair_order_id TEXT NOT NULL,
                username TEXT NOT NULL REFERENCES accounts(username),
                conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id),
                payload_json TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                PRIMARY KEY (username, repair_order_id)
            );
            INSERT INTO repair_orders (
                repair_order_id, username, conversation_id, payload_json, occurred_at
            )
            SELECT
                repair_order_id, username, conversation_id, payload_json, occurred_at
            FROM repair_orders_legacy;
            DROP TABLE repair_orders_legacy;
            """
        )

    @staticmethod
    def _repair_order_reference(username: str, sequence: int) -> str:
        account_code = re.sub(r"[^A-Z0-9]+", "-", username.upper()).strip("-")
        return f"SYN-RO-{account_code}-{sequence:04d}"

    def _migrate_repair_order_references(self) -> None:
        rows = self._execute(
            """
            SELECT username, repair_order_id, payload_json
            FROM repair_orders
            ORDER BY username, occurred_at, repair_order_id
            """
        ).fetchall()
        sequence_by_user: dict[str, int] = {}
        for row in rows:
            username = str(row["username"])
            sequence_by_user[username] = sequence_by_user.get(username, 0) + 1
            expected_prefix = f"SYN-RO-{re.sub(r'[^A-Z0-9]+', '-', username.upper()).strip('-')}-"
            if str(row["repair_order_id"]).startswith(expected_prefix):
                continue
            reference = self._repair_order_reference(
                username,
                sequence_by_user[username],
            )
            payload = json.loads(row["payload_json"])
            payload["repair_order_id"] = reference
            self._execute(
                """
                UPDATE repair_orders
                SET repair_order_id = ?, payload_json = ?
                WHERE username = ? AND repair_order_id = ?
                """,
                (
                    reference,
                    json.dumps(payload, ensure_ascii=False),
                    username,
                    row["repair_order_id"],
                ),
            )

    def _seed_accounts(self) -> None:
        with self._lock, self._connection:
            for username, password, role, display_name in PROTOTYPE_ACCOUNTS:
                if self._execute(
                    "SELECT 1 FROM accounts WHERE username = ?", (username,)
                ).fetchone():
                    continue
                salt = secrets.token_bytes(16)
                self._execute(
                    """
                    INSERT INTO accounts
                        (username, password_salt, password_hash, role, display_name)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (username, salt, _password_hash(password, salt), role, display_name),
                )

    def authenticate(self, username: str, password: str) -> dict[str, str] | None:
        with self._lock:
            row = self._execute("SELECT * FROM accounts WHERE username = ?", (username,)).fetchone()
        if row is None:
            _password_hash(password, bytes(16))
            return None
        supplied = _password_hash(password, row["password_salt"])
        if not hmac.compare_digest(supplied, row["password_hash"]):
            return None
        return {
            "username": row["username"],
            "role": row["role"],
            "display_name": row["display_name"],
            "language": row["language"],
        }

    def set_language(self, username: str, language: str) -> None:
        with self._lock, self._connection:
            self._execute(
                "UPDATE accounts SET language = ? WHERE username = ?",
                (language, username),
            )

    def create_conversation(self, username: str, conversation_id: str) -> None:
        occurred_at = _now()
        with self._lock, self._connection:
            self._execute(
                """
                INSERT INTO conversations
                    (conversation_id, username, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (conversation_id, username, occurred_at, occurred_at),
            )

    def latest_conversation(self, username: str) -> str | None:
        with self._lock:
            row = self._execute(
                """
                SELECT conversation_id FROM conversations
                WHERE username = ? ORDER BY updated_at DESC LIMIT 1
                """,
                (username,),
            ).fetchone()
        return None if row is None else str(row["conversation_id"])

    def owns_conversation(self, username: str, conversation_id: str) -> bool:
        with self._lock:
            return (
                self._execute(
                    """
                    SELECT 1 FROM conversations
                    WHERE username = ? AND conversation_id = ?
                    """,
                    (username, conversation_id),
                ).fetchone()
                is not None
            )

    def append_message(
        self,
        conversation_id: str,
        role: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        occurred_at = _now()
        metadata_json = None if metadata is None else json.dumps(metadata, ensure_ascii=False)
        with self._lock, self._connection:
            self._execute(
                """
                INSERT INTO messages
                    (conversation_id, role, text, metadata_json, occurred_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (conversation_id, role, text, metadata_json, occurred_at),
            )
            self._execute(
                "UPDATE conversations SET updated_at = ? WHERE conversation_id = ?",
                (occurred_at, conversation_id),
            )

    def delete_last_user_message(self, conversation_id: str) -> None:
        with self._lock, self._connection:
            self._execute(
                """
                DELETE FROM messages WHERE message_id = (
                    SELECT message_id FROM messages
                    WHERE conversation_id = ? AND role = 'user'
                    ORDER BY message_id DESC LIMIT 1
                )
                """,
                (conversation_id,),
            )

    def messages(self, username: str, conversation_id: str) -> list[dict[str, Any]]:
        if not self.owns_conversation(username, conversation_id):
            return []
        with self._lock:
            rows = self._execute(
                """
                SELECT role, text, metadata_json FROM messages
                WHERE conversation_id = ? ORDER BY message_id
                """,
                (conversation_id,),
            ).fetchall()
        return [
            {
                "role": row["role"],
                "text": row["text"],
                **({"metadata": json.loads(row["metadata_json"])} if row["metadata_json"] else {}),
            }
            for row in rows
        ]

    def add_history(self, username: str, entry: dict[str, Any]) -> None:
        with self._lock, self._connection:
            self._execute(
                """
                INSERT INTO service_history
                    (username, conversation_id, payload_json, occurred_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    username,
                    entry["conversation_id"],
                    json.dumps(entry, ensure_ascii=False),
                    entry["occurred_at"],
                ),
            )

    def add_repair_order(self, username: str, entry: dict[str, Any]) -> dict[str, Any]:
        with self._lock, self._connection:
            count = self._execute(
                "SELECT COUNT(*) AS count FROM repair_orders WHERE username = ?",
                (username,),
            ).fetchone()["count"]
            record = {
                "repair_order_id": self._repair_order_reference(username, count + 1),
                **entry,
            }
            self._execute(
                """
                INSERT INTO repair_orders
                    (repair_order_id, username, conversation_id, payload_json, occurred_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record["repair_order_id"],
                    username,
                    record["conversation_id"],
                    json.dumps(record, ensure_ascii=False),
                    record["occurred_at"],
                ),
            )
        return record

    def records(self, table: str, username: str) -> list[dict[str, Any]]:
        if table not in {"service_history", "repair_orders"}:
            raise ValueError("Unsupported record table.")
        with self._lock:
            rows = self._execute(
                f"""
                SELECT payload_json FROM {table}
                WHERE username = ? ORDER BY occurred_at DESC
                """,
                (username,),
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def admin_overview(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._execute(
                """
                SELECT
                    a.username, a.display_name, a.role, a.language,
                    COUNT(DISTINCT c.conversation_id) AS conversations,
                    COUNT(DISTINCT h.history_id) AS service_requests,
                    COUNT(DISTINCT r.repair_order_id) AS repair_orders
                FROM accounts a
                LEFT JOIN conversations c ON c.username = a.username
                LEFT JOIN service_history h ON h.username = a.username
                LEFT JOIN repair_orders r ON r.username = a.username
                GROUP BY a.username
                ORDER BY a.username
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def operational_summary(self) -> dict[str, Any]:
        with self._lock:
            totals = self._execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM accounts) AS accounts,
                    (SELECT COUNT(*) FROM conversations) AS conversations,
                    (SELECT COUNT(*) FROM service_history) AS service_requests,
                    (SELECT COUNT(*) FROM repair_orders) AS repair_orders
                """
            ).fetchone()
            history_rows = self._execute(
                """
                SELECT payload_json FROM service_history
                ORDER BY occurred_at DESC
                """
            ).fetchall()

        completion_statuses: dict[str, int] = {}
        service_statuses: dict[str, int] = {}
        protocols: dict[str, int] = {}
        for row in history_rows:
            entry = json.loads(row["payload_json"])
            completion = str(entry.get("completion_status", "unknown"))
            completion_statuses[completion] = completion_statuses.get(completion, 0) + 1
            for service in entry.get("services", []):
                status = str(service.get("status", "unknown"))
                protocol = str(service.get("protocol", "unknown"))
                service_statuses[status] = service_statuses.get(status, 0) + 1
                if service.get("called"):
                    protocols[protocol] = protocols.get(protocol, 0) + 1
        return {
            **dict(totals),
            "completion_statuses": completion_statuses,
            "service_statuses": service_statuses,
            "protocol_invocations": protocols,
        }

    def search_conversations(
        self,
        query: str,
        *,
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        normalized = query.strip()
        escaped = normalized.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        with self._lock:
            rows = self._execute(
                """
                SELECT
                    c.conversation_id,
                    c.username,
                    a.display_name,
                    c.created_at,
                    c.updated_at,
                    (SELECT COUNT(*) FROM messages count_messages
                     WHERE count_messages.conversation_id = c.conversation_id)
                        AS message_count,
                    (SELECT snippet.text FROM messages snippet
                     WHERE snippet.conversation_id = c.conversation_id
                       AND (? = '' OR snippet.text LIKE ? ESCAPE '\\')
                     ORDER BY snippet.message_id DESC LIMIT 1)
                        AS match_text,
                    (SELECT matched_order.repair_order_id
                      FROM repair_orders matched_order
                      WHERE matched_order.username = c.username
                        AND matched_order.conversation_id = c.conversation_id
                        AND matched_order.repair_order_id LIKE ? ESCAPE '\\'
                      ORDER BY matched_order.occurred_at DESC LIMIT 1)
                        AS match_repair_order
                FROM conversations c
                JOIN accounts a ON a.username = c.username
                WHERE ? = ''
                   OR c.username LIKE ? ESCAPE '\\'
                   OR a.display_name LIKE ? ESCAPE '\\'
                   OR EXISTS (
                       SELECT 1 FROM messages matched
                       WHERE matched.conversation_id = c.conversation_id
                         AND matched.text LIKE ? ESCAPE '\\'
                   )
                   OR EXISTS (
                       SELECT 1 FROM repair_orders matched_order
                       WHERE matched_order.username = c.username
                         AND matched_order.conversation_id = c.conversation_id
                         AND matched_order.repair_order_id LIKE ? ESCAPE '\\'
                   )
                ORDER BY c.updated_at DESC
                LIMIT ?
                """,
                (
                    normalized,
                    pattern,
                    pattern,
                    normalized,
                    pattern,
                    pattern,
                    pattern,
                    pattern,
                    limit,
                ),
            ).fetchall()
        return [
            {
                **dict(row),
                "match_text": str(row["match_text"] or "")[:240],
            }
            for row in rows
        ]

    def conversation_for_administrator(self, conversation_id: str) -> dict[str, Any] | None:
        with self._lock:
            conversation = self._execute(
                """
                SELECT c.*, a.display_name
                FROM conversations c
                JOIN accounts a ON a.username = c.username
                WHERE c.conversation_id = ?
                """,
                (conversation_id,),
            ).fetchone()
            if conversation is None:
                return None
            rows = self._execute(
                """
                SELECT role, text, metadata_json, occurred_at
                FROM messages WHERE conversation_id = ?
                ORDER BY message_id
                """,
                (conversation_id,),
            ).fetchall()
            history_rows = self._execute(
                """
                SELECT payload_json FROM service_history
                WHERE username = ? AND conversation_id = ?
                ORDER BY occurred_at DESC
                """,
                (conversation["username"], conversation_id),
            ).fetchall()
            repair_order_rows = self._execute(
                """
                SELECT payload_json FROM repair_orders
                WHERE username = ? AND conversation_id = ?
                ORDER BY occurred_at DESC
                """,
                (conversation["username"], conversation_id),
            ).fetchall()
        messages = [
            {
                "role": row["role"],
                "text": row["text"],
                "occurred_at": row["occurred_at"],
                **({"metadata": json.loads(row["metadata_json"])} if row["metadata_json"] else {}),
            }
            for row in rows
        ]
        return {
            **dict(conversation),
            "messages": messages,
            "service_history": [json.loads(row["payload_json"]) for row in history_rows],
            "repair_orders": [json.loads(row["payload_json"]) for row in repair_order_rows],
        }
