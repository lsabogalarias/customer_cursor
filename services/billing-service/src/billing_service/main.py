"""Composition root for the billing service."""

import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from portal_common.fastapi_auth import build_require_auth

from billing_service.adapters.http import create_app
from billing_service.adapters.mock_gateway import InMemoryPaymentGateway
from billing_service.adapters.sqlite_payments import SqlitePaymentRepository
from billing_service.domain.use_cases import ListPayments, PayPending


def build_app() -> FastAPI:
    """Wire adapters and use cases.

    Returns:
        The billing FastAPI application.

    Environment variables:
        JWT_SECRET: HMAC secret. Defaults to the local demo placeholder.
        DATABASE_PATH: SQLite file. Defaults to ``data/billing.db``.
    """
    secret = os.environ.get("JWT_SECRET", "dev-only-change-me")
    database_path = Path(
        os.environ.get(
            "DATABASE_PATH",
            str(Path(__file__).resolve().parents[2] / "data" / "billing.db"),
        )
    )
    payments = SqlitePaymentRepository(database_path)
    payments.seed_demo()
    return create_app(
        list_payments=ListPayments(payments),
        pay_pending=PayPending(payments, InMemoryPaymentGateway()),
        require_auth=build_require_auth(secret),
    )


app = build_app()


def main() -> None:
    """Serve the billing API.

    Environment variables:
        PORT: Listen port. Defaults to 8003.
    """
    port = int(os.environ.get("PORT", "8003"))
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
