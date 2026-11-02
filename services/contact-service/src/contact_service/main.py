"""Composition root for the contact service."""

import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from portal_common.fastapi_auth import build_require_auth

from contact_service.adapters.http import create_app
from contact_service.adapters.sqlite_contact import SqliteContactRepository
from contact_service.adapters.twilio_mock import InMemoryTwilio
from contact_service.domain.use_cases import ListCalls, ListMessages, SendMessage, StartCall


def build_app() -> FastAPI:
    """Wire adapters and use cases.

    Returns:
        The contact FastAPI application.

    Environment variables:
        JWT_SECRET: HMAC secret. Defaults to the local demo placeholder.
        DATABASE_PATH: SQLite file. Defaults to ``data/contact.db``.
    """
    secret = os.environ.get("JWT_SECRET", "dev-only-change-me")
    database_path = Path(
        os.environ.get(
            "DATABASE_PATH",
            str(Path(__file__).resolve().parents[2] / "data" / "contact.db"),
        )
    )
    history = SqliteContactRepository(database_path)
    twilio = InMemoryTwilio()
    return create_app(
        send_message=SendMessage(history, twilio),
        list_messages=ListMessages(history),
        start_call=StartCall(history, twilio),
        list_calls=ListCalls(history),
        require_auth=build_require_auth(secret),
    )


app = build_app()


def main() -> None:
    """Serve the contact API.

    Environment variables:
        PORT: Listen port. Defaults to 8004.
    """
    port = int(os.environ.get("PORT", "8004"))
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
