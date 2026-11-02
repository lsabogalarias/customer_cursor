"""SQLite account repository."""

import sqlite3
from pathlib import Path

from portal_common.demo import DEMO_EMAIL, DEMO_FULL_NAME, DEMO_USER_ID
from portal_common.identity import AuthContext

from identity_service.domain.models import StoredUser


def _required_str(row: sqlite3.Row, column: str) -> str:
    """Read a text column.

    Args:
        row: SQLite result row.
        column: Column name.

    Returns:
        The column value.

    Raises:
        RuntimeError: The column is missing or not text.
    """
    value: object = row[column]
    if not isinstance(value, str):
        raise RuntimeError(f"Column {column} is not text.")
    return value


class SqliteUserRepository:
    """Stores customer accounts in a local SQLite file."""

    def __init__(self, database_path: Path) -> None:
        """Create the database file and schema when they are missing.

        Args:
            database_path: Path to the SQLite file.
        """
        self._path = database_path
        database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    full_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL
                )
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

    def find_by_email(self, email: str) -> StoredUser | None:
        """Load an account by normalized email.

        Args:
            email: Normalized email address.

        Returns:
            The stored account, or None when the address is unknown.
        """
        with self._connect() as connection:
            row = connection.execute(
                "SELECT user_id, email, full_name, password_hash FROM users WHERE email = ?",
                (email,),
            ).fetchone()
        if row is None:
            return None
        return self._map(row)

    def add(self, user: StoredUser) -> None:
        """Insert a new account.

        Args:
            user: Account to persist, including the password hash.
        """
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO users (user_id, email, full_name, password_hash)
                VALUES (?, ?, ?, ?)
                """,
                (user.user_id, user.email, user.full_name, user.password_hash),
            )

    def find_by_id(self, auth: AuthContext) -> StoredUser | None:
        """Load the account that belongs to the verified caller.

        Args:
            auth: Identity taken from the verified JWT.

        Returns:
            The caller's account, or None when it does not exist.
        """
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT user_id, email, full_name, password_hash
                FROM users
                WHERE user_id = ?
                """,
                (auth.user_id,),
            ).fetchone()
        if row is None:
            return None
        return self._map(row)

    def seed_demo(self, password_hash: str) -> None:
        """Insert the published demo customer when the email is absent.

        This startup seed is an adapter concern. Use cases never call it.

        Args:
            password_hash: Argon2 hash of the published demo password.
        """
        if self.find_by_email(DEMO_EMAIL) is not None:
            return
        self.add(
            StoredUser(
                user_id=DEMO_USER_ID,
                email=DEMO_EMAIL,
                full_name=DEMO_FULL_NAME,
                password_hash=password_hash,
            )
        )

    def _map(self, row: sqlite3.Row) -> StoredUser:
        """Map a row to a domain account.

        Args:
            row: SQLite result row.

        Returns:
            Stored account.
        """
        return StoredUser(
            user_id=_required_str(row, "user_id"),
            email=_required_str(row, "email"),
            full_name=_required_str(row, "full_name"),
            password_hash=_required_str(row, "password_hash"),
        )
