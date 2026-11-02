"""SQLite repository for policies, vehicles, drivers, documents, and claims."""

import sqlite3
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from portal_common.demo import DEMO_FULL_NAME, DEMO_USER_ID
from portal_common.identity import AuthContext

from policy_service.domain.models import (
    Claim,
    DocumentFile,
    DocumentSummary,
    Driver,
    LineOfBusiness,
    Policy,
    PolicyStatus,
    Vehicle,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS policies (
    policy_number TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    line_of_business TEXT NOT NULL,
    product_name TEXT NOT NULL,
    status TEXT NOT NULL,
    insured_name TEXT NOT NULL,
    property_address TEXT,
    effective_date TEXT NOT NULL,
    expiration_date TEXT NOT NULL,
    premium TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id TEXT PRIMARY KEY,
    policy_number TEXT NOT NULL,
    user_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    vin TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS drivers (
    driver_id TEXT PRIMARY KEY,
    policy_number TEXT NOT NULL,
    user_id TEXT NOT NULL,
    full_name TEXT NOT NULL,
    license_number TEXT NOT NULL,
    date_of_birth TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    policy_number TEXT NOT NULL,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    file_name TEXT NOT NULL,
    content_type TEXT NOT NULL,
    body TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY,
    policy_number TEXT NOT NULL,
    user_id TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    filed_at TEXT NOT NULL
);
"""


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


def _integer(row: sqlite3.Row, column: str) -> int:
    """Read a required integer column.

    Args:
        row: SQLite result row.
        column: Column name.

    Returns:
        The column value.

    Raises:
        RuntimeError: The column is not an integer.
    """
    value: object = row[column]
    if not isinstance(value, int):
        raise RuntimeError(f"Column {column} is not an integer.")
    return value


def _policy(row: sqlite3.Row) -> Policy:
    """Map a policy row.

    Args:
        row: SQLite result row.

    Returns:
        Domain policy.
    """
    return Policy(
        policy_number=_text(row, "policy_number"),
        user_id=_text(row, "user_id"),
        line_of_business=LineOfBusiness(_text(row, "line_of_business")),
        product_name=_text(row, "product_name"),
        status=PolicyStatus(_text(row, "status")),
        insured_name=_text(row, "insured_name"),
        property_address=_optional_text(row, "property_address"),
        effective_date=date.fromisoformat(_text(row, "effective_date")),
        expiration_date=date.fromisoformat(_text(row, "expiration_date")),
        premium=Decimal(_text(row, "premium")),
    )


class SqlitePolicyRepository:
    """Stores policy data in a local SQLite file."""

    def __init__(self, database_path: Path) -> None:
        """Create the database file and schema when they are missing.

        Args:
            database_path: Path to the SQLite file.
        """
        self._path = database_path
        database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        """Open a connection that returns rows by column name.

        Returns:
            A new SQLite connection.
        """
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection

    def seed_demo(self) -> None:
        """Insert the published demo policies when they are absent.

        This startup seed is an adapter concern. Use cases never call it.
        """
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS total FROM policies WHERE user_id = ?",
                (DEMO_USER_ID,),
            ).fetchone()
            total = 0 if row is None else row["total"]
            if isinstance(total, int) and total > 0:
                return
            self._insert_demo(connection)

    def list_policies(self, auth: AuthContext) -> list[Policy]:
        """List the caller's policies.

        Args:
            auth: Verified caller.

        Returns:
            Policies owned by the caller, ordered by policy number.
        """
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM policies
                WHERE user_id = ?
                ORDER BY policy_number
                """,
                (auth.user_id,),
            ).fetchall()
        return [_policy(row) for row in rows]

    def get_policy(self, auth: AuthContext, policy_number: str) -> Policy | None:
        """Load one policy when the caller owns it.

        Args:
            auth: Verified caller.
            policy_number: Normalized policy number.

        Returns:
            The policy, or None.
        """
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM policies WHERE user_id = ? AND policy_number = ?",
                (auth.user_id, policy_number),
            ).fetchone()
        if row is None:
            return None
        return _policy(row)

    def save_status(
        self, auth: AuthContext, policy_number: str, status: PolicyStatus
    ) -> Policy | None:
        """Update status when the caller owns the policy.

        Args:
            auth: Verified caller.
            policy_number: Normalized policy number.
            status: New status.

        Returns:
            The updated policy, or None when it is not owned.
        """
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE policies SET status = ?
                WHERE user_id = ? AND policy_number = ?
                """,
                (status.value, auth.user_id, policy_number),
            )
            if cursor.rowcount != 1:
                return None
        return self.get_policy(auth, policy_number)

    def list_vehicles(self, auth: AuthContext, policy_number: str) -> list[Vehicle]:
        """List vehicles on a policy the caller owns.

        Args:
            auth: Verified caller.
            policy_number: Normalized policy number.

        Returns:
            Vehicles, or an empty list.
        """
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM vehicles
                WHERE user_id = ? AND policy_number = ?
                ORDER BY make, model
                """,
                (auth.user_id, policy_number),
            ).fetchall()
        return [
            Vehicle(
                vehicle_id=_text(row, "vehicle_id"),
                policy_number=_text(row, "policy_number"),
                year=_integer(row, "year"),
                make=_text(row, "make"),
                model=_text(row, "model"),
                vin=_text(row, "vin"),
            )
            for row in rows
        ]

    def add_vehicle(self, auth: AuthContext, vehicle: Vehicle) -> bool:
        """Insert a vehicle when the caller owns the policy.

        Args:
            auth: Verified caller.
            vehicle: Vehicle to insert.

        Returns:
            True when a row was inserted.
        """
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO vehicles (
                    vehicle_id, policy_number, user_id, year, make, model, vin
                )
                SELECT ?, ?, ?, ?, ?, ?, ?
                WHERE EXISTS (
                    SELECT 1 FROM policies
                    WHERE policy_number = ? AND user_id = ?
                )
                """,
                (
                    vehicle.vehicle_id,
                    vehicle.policy_number,
                    auth.user_id,
                    vehicle.year,
                    vehicle.make,
                    vehicle.model,
                    vehicle.vin,
                    vehicle.policy_number,
                    auth.user_id,
                ),
            )
        return cursor.rowcount == 1

    def remove_vehicle(self, auth: AuthContext, policy_number: str, vehicle_id: str) -> bool:
        """Delete a vehicle when the caller owns it.

        Args:
            auth: Verified caller.
            policy_number: Normalized policy number.
            vehicle_id: Vehicle identifier.

        Returns:
            True when a row was deleted.
        """
        with self._connect() as connection:
            cursor = connection.execute(
                """
                DELETE FROM vehicles
                WHERE user_id = ? AND policy_number = ? AND vehicle_id = ?
                """,
                (auth.user_id, policy_number, vehicle_id),
            )
        return cursor.rowcount == 1

    def list_drivers(self, auth: AuthContext, policy_number: str) -> list[Driver]:
        """List drivers on a policy the caller owns.

        Args:
            auth: Verified caller.
            policy_number: Normalized policy number.

        Returns:
            Drivers, or an empty list.
        """
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM drivers
                WHERE user_id = ? AND policy_number = ?
                ORDER BY full_name
                """,
                (auth.user_id, policy_number),
            ).fetchall()
        return [
            Driver(
                driver_id=_text(row, "driver_id"),
                policy_number=_text(row, "policy_number"),
                full_name=_text(row, "full_name"),
                license_number=_text(row, "license_number"),
                date_of_birth=date.fromisoformat(_text(row, "date_of_birth")),
            )
            for row in rows
        ]

    def add_driver(self, auth: AuthContext, driver: Driver) -> bool:
        """Insert a driver when the caller owns the policy.

        Args:
            auth: Verified caller.
            driver: Driver to insert.

        Returns:
            True when a row was inserted.
        """
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO drivers (
                    driver_id, policy_number, user_id, full_name, license_number, date_of_birth
                )
                SELECT ?, ?, ?, ?, ?, ?
                WHERE EXISTS (
                    SELECT 1 FROM policies
                    WHERE policy_number = ? AND user_id = ?
                )
                """,
                (
                    driver.driver_id,
                    driver.policy_number,
                    auth.user_id,
                    driver.full_name,
                    driver.license_number,
                    driver.date_of_birth.isoformat(),
                    driver.policy_number,
                    auth.user_id,
                ),
            )
        return cursor.rowcount == 1

    def remove_driver(self, auth: AuthContext, policy_number: str, driver_id: str) -> bool:
        """Delete a driver when the caller owns it.

        Args:
            auth: Verified caller.
            policy_number: Normalized policy number.
            driver_id: Driver identifier.

        Returns:
            True when a row was deleted.
        """
        with self._connect() as connection:
            cursor = connection.execute(
                """
                DELETE FROM drivers
                WHERE user_id = ? AND policy_number = ? AND driver_id = ?
                """,
                (auth.user_id, policy_number, driver_id),
            )
        return cursor.rowcount == 1

    def list_documents(
        self, auth: AuthContext, policy_number: str | None
    ) -> list[DocumentSummary]:
        """List document metadata for the caller.

        Args:
            auth: Verified caller.
            policy_number: Optional policy filter.

        Returns:
            Document summaries.
        """
        query = """
            SELECT document_id, policy_number, title, file_name, content_type
            FROM documents
            WHERE user_id = ?
        """
        parameters: list[str] = [auth.user_id]
        if policy_number is not None:
            query += " AND policy_number = ?"
            parameters.append(policy_number)
        query += " ORDER BY policy_number, title"
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [
            DocumentSummary(
                document_id=_text(row, "document_id"),
                policy_number=_text(row, "policy_number"),
                title=_text(row, "title"),
                file_name=_text(row, "file_name"),
                content_type=_text(row, "content_type"),
            )
            for row in rows
        ]

    def get_document(self, auth: AuthContext, document_id: str) -> DocumentFile | None:
        """Load a document body when the caller owns it.

        Args:
            auth: Verified caller.
            document_id: Document identifier.

        Returns:
            The file, or None.
        """
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT document_id, policy_number, title, file_name, content_type, body
                FROM documents
                WHERE user_id = ? AND document_id = ?
                """,
                (auth.user_id, document_id),
            ).fetchone()
        if row is None:
            return None
        return DocumentFile(
            document_id=_text(row, "document_id"),
            policy_number=_text(row, "policy_number"),
            title=_text(row, "title"),
            file_name=_text(row, "file_name"),
            content_type=_text(row, "content_type"),
            body=_text(row, "body"),
        )

    def add_claim(self, auth: AuthContext, claim: Claim) -> bool:
        """Insert a claim when the caller owns the policy.

        Args:
            auth: Verified caller.
            claim: Claim to insert.

        Returns:
            True when a row was inserted.
        """
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO claims (
                    claim_id, policy_number, user_id, description, status, filed_at
                )
                SELECT ?, ?, ?, ?, ?, ?
                WHERE EXISTS (
                    SELECT 1 FROM policies
                    WHERE policy_number = ? AND user_id = ?
                )
                """,
                (
                    claim.claim_id,
                    claim.policy_number,
                    auth.user_id,
                    claim.description,
                    claim.status,
                    claim.filed_at.isoformat(),
                    claim.policy_number,
                    auth.user_id,
                ),
            )
        return cursor.rowcount == 1

    def list_claims(self, auth: AuthContext, policy_number: str) -> list[Claim]:
        """List claims on a policy the caller owns.

        Args:
            auth: Verified caller.
            policy_number: Normalized policy number.

        Returns:
            Claims, oldest first.
        """
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM claims
                WHERE user_id = ? AND policy_number = ?
                ORDER BY filed_at
                """,
                (auth.user_id, policy_number),
            ).fetchall()
        return [
            Claim(
                claim_id=_text(row, "claim_id"),
                policy_number=_text(row, "policy_number"),
                description=_text(row, "description"),
                status=_text(row, "status"),
                filed_at=datetime.fromisoformat(_text(row, "filed_at")),
            )
            for row in rows
        ]

    def _insert_demo(self, connection: sqlite3.Connection) -> None:
        """Insert the three demo policies and their related rows.

        Args:
            connection: Open SQLite connection.
        """
        policies = [
            (
                "AUTO-1001",
                DEMO_USER_ID,
                "personal_auto",
                "Personal Auto",
                "active",
                DEMO_FULL_NAME,
                None,
                "2026-01-01",
                "2027-01-01",
                "1280.00",
            ),
            (
                "AUTO-2044",
                DEMO_USER_ID,
                "truck",
                "Commercial Truck",
                "active",
                DEMO_FULL_NAME,
                None,
                "2026-01-01",
                "2027-01-01",
                "3420.50",
            ),
            (
                "HOME-3008",
                DEMO_USER_ID,
                "homeowners",
                "Homeowners",
                "active",
                DEMO_FULL_NAME,
                "18 Cedar Lane, Austin, TX 78701",
                "2026-01-01",
                "2027-01-01",
                "980.00",
            ),
        ]
        connection.executemany(
            """
            INSERT INTO policies (
                policy_number, user_id, line_of_business, product_name, status,
                insured_name, property_address, effective_date, expiration_date, premium
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            policies,
        )
        connection.executemany(
            """
            INSERT INTO vehicles (
                vehicle_id, policy_number, user_id, year, make, model, vin
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "veh-auto-1001",
                    "AUTO-1001",
                    DEMO_USER_ID,
                    2022,
                    "Toyota",
                    "Camry",
                    "4T1BF1FK5CU123456",
                ),
                (
                    "veh-auto-2044",
                    "AUTO-2044",
                    DEMO_USER_ID,
                    2020,
                    "Freightliner",
                    "Cascadia",
                    "1FUJGLDR0LLBC1234",
                ),
            ],
        )
        connection.executemany(
            """
            INSERT INTO drivers (
                driver_id, policy_number, user_id, full_name, license_number, date_of_birth
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "drv-auto-1001",
                    "AUTO-1001",
                    DEMO_USER_ID,
                    DEMO_FULL_NAME,
                    "D1234567",
                    "1988-04-12",
                ),
                (
                    "drv-auto-2044",
                    "AUTO-2044",
                    DEMO_USER_ID,
                    DEMO_FULL_NAME,
                    "D1234567",
                    "1988-04-12",
                ),
            ],
        )
        documents = [
            (
                "doc-auto-1001-dec",
                "AUTO-1001",
                "Declarations Page",
                "AUTO-1001-declarations.txt",
                "Personal auto declarations for Alex Morgan. Term premium 1280.00.",
            ),
            (
                "doc-auto-1001-id",
                "AUTO-1001",
                "Insurance ID Card",
                "AUTO-1001-id-card.txt",
                "Insurance ID card. Policy AUTO-1001. Vehicle 2022 Toyota Camry.",
            ),
            (
                "doc-auto-2044-dec",
                "AUTO-2044",
                "Declarations Page",
                "AUTO-2044-declarations.txt",
                "Commercial truck declarations for Alex Morgan. Term premium 3420.50.",
            ),
            (
                "doc-auto-2044-id",
                "AUTO-2044",
                "Insurance ID Card",
                "AUTO-2044-id-card.txt",
                "Insurance ID card. Policy AUTO-2044. Vehicle 2020 Freightliner Cascadia.",
            ),
            (
                "doc-home-3008-dec",
                "HOME-3008",
                "Declarations Page",
                "HOME-3008-declarations.txt",
                "Homeowners declarations for 18 Cedar Lane, Austin, TX 78701.",
            ),
            (
                "doc-home-3008-contract",
                "HOME-3008",
                "Policy Contract",
                "HOME-3008-contract.txt",
                "Homeowners policy contract for policy HOME-3008.",
            ),
        ]
        connection.executemany(
            """
            INSERT INTO documents (
                document_id, policy_number, user_id, title, file_name, content_type, body
            ) VALUES (?, ?, ?, ?, ?, 'text/plain', ?)
            """,
            [
                (document_id, policy_number, DEMO_USER_ID, title, file_name, body)
                for document_id, policy_number, title, file_name, body in documents
            ],
        )
