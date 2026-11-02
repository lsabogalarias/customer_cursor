"""SQLite payment repository."""

import sqlite3
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from portal_common.demo import DEMO_USER_ID
from portal_common.identity import AuthContext

from billing_service.domain.models import Payment, PaymentStatus


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


def _optional_text(row: sqlite3.Row, column: str) -> str | None:
    """Read an optional text column.

    Args:
        row: SQLite result row.
        column: Column name.

    Returns:
        The column value, or None.

    Raises:
        RuntimeError: The column is neither text nor null.
    """
    value: object = row[column]
    if value is None:
        return None
    if not isinstance(value, str):
        raise RuntimeError(f"Column {column} is not text.")
    return value


def _payment(row: sqlite3.Row) -> Payment:
    """Map a payment row.

    Args:
        row: SQLite result row.

    Returns:
        Domain payment.
    """
    paid_at = _optional_text(row, "paid_at")
    return Payment(
        payment_id=_text(row, "payment_id"),
        user_id=_text(row, "user_id"),
        policy_number=_text(row, "policy_number"),
        amount=Decimal(_text(row, "amount")),
        status=PaymentStatus(_text(row, "status")),
        due_date=date.fromisoformat(_text(row, "due_date")),
        description=_text(row, "description"),
        paid_at=None if paid_at is None else datetime.fromisoformat(paid_at),
        confirmation_id=_optional_text(row, "confirmation_id"),
    )


class SqlitePaymentRepository:
    """Stores payments in a local SQLite file."""

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
                CREATE TABLE IF NOT EXISTS payments (
                    payment_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    policy_number TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    status TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    description TEXT NOT NULL,
                    paid_at TEXT,
                    confirmation_id TEXT
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

    def seed_demo(self) -> None:
        """Insert the published demo payments when they are absent.

        This startup seed is an adapter concern. Use cases never call it.
        """
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM payments").fetchone()
            total: object = 0 if row is None else row["total"]
            if isinstance(total, int) and total > 0:
                return
            connection.executemany(
                """
                INSERT INTO payments (
                    payment_id, user_id, policy_number, amount, status, due_date,
                    description, paid_at, confirmation_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        "pay-auto-1001-1",
                        DEMO_USER_ID,
                        "AUTO-1001",
                        "640.00",
                        "paid",
                        "2026-06-01",
                        "Installment 1 of 2",
                        "2026-06-02T15:00:00+00:00",
                        "mock-seeded-1001",
                    ),
                    (
                        "pay-auto-1001-2",
                        DEMO_USER_ID,
                        "AUTO-1001",
                        "640.00",
                        "pending",
                        "2026-12-01",
                        "Installment 2 of 2",
                        None,
                        None,
                    ),
                    (
                        "pay-auto-2044-1",
                        DEMO_USER_ID,
                        "AUTO-2044",
                        "1710.25",
                        "paid",
                        "2026-06-01",
                        "Installment 1 of 2",
                        "2026-06-02T15:00:00+00:00",
                        "mock-seeded-2044",
                    ),
                    (
                        "pay-auto-2044-2",
                        DEMO_USER_ID,
                        "AUTO-2044",
                        "1710.25",
                        "pending",
                        "2026-12-01",
                        "Installment 2 of 2",
                        None,
                        None,
                    ),
                    (
                        "pay-home-3008-1",
                        DEMO_USER_ID,
                        "HOME-3008",
                        "980.00",
                        "pending",
                        "2026-03-01",
                        "Annual homeowners premium",
                        None,
                        None,
                    ),
                ],
            )

    def list_payments(self, auth: AuthContext, policy_number: str | None) -> list[Payment]:
        """List payments for the caller.

        Args:
            auth: Verified caller.
            policy_number: Optional policy filter.

        Returns:
            Payments owned by the caller.
        """
        query = "SELECT * FROM payments WHERE user_id = ?"
        parameters: list[str] = [auth.user_id]
        if policy_number is not None:
            query += " AND policy_number = ?"
            parameters.append(policy_number)
        query += " ORDER BY due_date, payment_id"
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [_payment(row) for row in rows]

    def get_payment(self, auth: AuthContext, payment_id: str) -> Payment | None:
        """Load one payment when the caller owns it.

        Args:
            auth: Verified caller.
            payment_id: Payment identifier.

        Returns:
            The payment, or None.
        """
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM payments WHERE user_id = ? AND payment_id = ?",
                (auth.user_id, payment_id),
            ).fetchone()
        if row is None:
            return None
        return _payment(row)

    def mark_paid(
        self,
        auth: AuthContext,
        payment_id: str,
        paid_at: datetime,
        confirmation_id: str,
    ) -> Payment | None:
        """Mark a pending payment paid when the caller owns it.

        Args:
            auth: Verified caller.
            payment_id: Payment identifier.
            paid_at: Timestamp recorded for the mock charge.
            confirmation_id: Confirmation id from the mock gateway.

        Returns:
            The updated payment, or None when it is not an owned pending row.
        """
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE payments
                SET status = 'paid', paid_at = ?, confirmation_id = ?
                WHERE user_id = ? AND payment_id = ? AND status = 'pending'
                """,
                (paid_at.isoformat(), confirmation_id, auth.user_id, payment_id),
            )
            if cursor.rowcount != 1:
                return None
        return self.get_payment(auth, payment_id)
