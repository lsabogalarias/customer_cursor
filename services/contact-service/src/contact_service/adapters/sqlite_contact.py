"""SQLite history for messages and calls."""

import sqlite3
from datetime import datetime
from pathlib import Path

from portal_common.identity import AuthContext

from contact_service.domain.models import AgentCall, AgentMessage


def _text(row: sqlite3.Row, column: str) -> str:
    """Read a required text column.

    Args:
        row: SQLite result row.
        column: Column name.

    Returns:
        The column value.

    Raises:
        RuntimeError: The column is not text.
    """
    value: object = row[column]
    if not isinstance(value, str):
        raise RuntimeError(f"Column {column} is not text.")
    return value


class SqliteContactRepository:
    """Stores messages and calls in a local SQLite file."""

    def __init__(self, database_path: Path) -> None:
        """Create the database file and schema when they are missing.

        Args:
            database_path: Path to the SQLite file.
        """
        self._path = database_path
        database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    body TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    twilio_sid TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS calls (
                    call_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    twilio_sid TEXT NOT NULL
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        """Open a connection that returns rows by column name.

        Returns:
            A new SQLite connection.
        """
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection

    def add(self, auth: AuthContext, message: AgentMessage) -> None:
        """Store a message for the caller.

        This method satisfies MessageRepository. CallRepository uses ``add_call``.

        Args:
            auth: Verified caller.
            message: Message to persist.
        """
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO messages (message_id, user_id, body, created_at, twilio_sid)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    message.message_id,
                    auth.user_id,
                    message.body,
                    message.created_at.isoformat(),
                    message.twilio_sid,
                ),
            )

    def list_messages(self, auth: AuthContext) -> list[AgentMessage]:
        """List the caller's messages.

        Args:
            auth: Verified caller.

        Returns:
            Messages, oldest first.
        """
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM messages
                WHERE user_id = ?
                ORDER BY created_at
                """,
                (auth.user_id,),
            ).fetchall()
        return [
            AgentMessage(
                message_id=_text(row, "message_id"),
                body=_text(row, "body"),
                created_at=datetime.fromisoformat(_text(row, "created_at")),
                twilio_sid=_text(row, "twilio_sid"),
            )
            for row in rows
        ]

    def add_call(self, auth: AuthContext, call: AgentCall) -> None:
        """Store a call for the caller.

        Args:
            auth: Verified caller.
            call: Call to persist.
        """
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO calls (call_id, user_id, phone_number, created_at, twilio_sid)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    call.call_id,
                    auth.user_id,
                    call.phone_number,
                    call.created_at.isoformat(),
                    call.twilio_sid,
                ),
            )

    def list_calls(self, auth: AuthContext) -> list[AgentCall]:
        """List the caller's calls.

        Args:
            auth: Verified caller.

        Returns:
            Calls, oldest first.
        """
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM calls
                WHERE user_id = ?
                ORDER BY created_at
                """,
                (auth.user_id,),
            ).fetchall()
        return [
            AgentCall(
                call_id=_text(row, "call_id"),
                phone_number=_text(row, "phone_number"),
                created_at=datetime.fromisoformat(_text(row, "created_at")),
                twilio_sid=_text(row, "twilio_sid"),
            )
            for row in rows
        ]
