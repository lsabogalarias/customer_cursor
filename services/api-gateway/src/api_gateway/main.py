"""Composition root for the API gateway."""

import os

import uvicorn
from fastapi import FastAPI

from api_gateway.adapters.http import create_app
from api_gateway.adapters.httpx_client import HttpxUpstreamClient


def build_app() -> FastAPI:
    """Read upstream URLs and build the gateway.

    Returns:
        The gateway FastAPI application.

    Environment variables:
        JWT_SECRET: HMAC secret. Defaults to the local demo placeholder.
        IDENTITY_URL: Identity base URL. Defaults to http://127.0.0.1:8001.
        POLICY_URL: Policy base URL. Defaults to http://127.0.0.1:8002.
        BILLING_URL: Billing base URL. Defaults to http://127.0.0.1:8003.
        CONTACT_URL: Contact base URL. Defaults to http://127.0.0.1:8004.
    """
    secret = os.environ.get("JWT_SECRET", "dev-only-change-me")
    identity_url = os.environ.get("IDENTITY_URL", "http://127.0.0.1:8001")
    policy_url = os.environ.get("POLICY_URL", "http://127.0.0.1:8002")
    billing_url = os.environ.get("BILLING_URL", "http://127.0.0.1:8003")
    contact_url = os.environ.get("CONTACT_URL", "http://127.0.0.1:8004")
    return create_app(
        secret=secret,
        upstreams={
            "auth": identity_url,
            "policies": policy_url,
            "documents": policy_url,
            "payments": billing_url,
            "contact": contact_url,
        },
        client=HttpxUpstreamClient(),
    )


app = build_app()


def main() -> None:
    """Serve the gateway.

    Environment variables:
        PORT: Listen port. Defaults to 8000.
    """
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
