"""Composition root for the identity service."""

import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from portal_common.demo import DEMO_PASSWORD
from portal_common.fastapi_auth import build_require_auth

from identity_service.adapters.http import create_app
from identity_service.adapters.password import Argon2PasswordHasher
from identity_service.adapters.sqlite_users import SqliteUserRepository
from identity_service.adapters.tokens import JwtTokenIssuer
from identity_service.domain.use_cases import GetCurrentUser, LoginUser, RegisterUser

_TTL_SECONDS = 3600


def build_app() -> FastAPI:
    """Wire adapters and use cases.

    Returns:
        The identity FastAPI application.

    Environment variables:
        JWT_SECRET: HMAC secret. Defaults to the local demo placeholder.
        DATABASE_PATH: SQLite file. Defaults to ``data/identity.db``.
    """
    secret = os.environ.get("JWT_SECRET", "dev-only-change-me")
    database_path = Path(
        os.environ.get(
            "DATABASE_PATH",
            str(Path(__file__).resolve().parents[2] / "data" / "identity.db"),
        )
    )
    hasher = Argon2PasswordHasher()
    users = SqliteUserRepository(database_path)
    users.seed_demo(hasher.hash_password(DEMO_PASSWORD))
    tokens = JwtTokenIssuer(secret, _TTL_SECONDS)
    return create_app(
        register_user=RegisterUser(users, hasher),
        login_user=LoginUser(users, hasher, tokens, _TTL_SECONDS),
        get_current_user=GetCurrentUser(users),
        require_auth=build_require_auth(secret),
    )


app = build_app()


def main() -> None:
    """Serve the identity API.

    Environment variables:
        PORT: Listen port. Defaults to 8001.
    """
    port = int(os.environ.get("PORT", "8001"))
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
