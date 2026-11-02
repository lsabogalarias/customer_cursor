"""HTTP adapter for the API gateway."""

from collections.abc import Mapping

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from portal_common.errors import TokenError
from portal_common.tokens import verify_access_token

from api_gateway.domain.routing import is_public, normalize_path, resolve_upstream
from api_gateway.ports.outbound import UpstreamClient


def create_app(secret: str, upstreams: Mapping[str, str], client: UpstreamClient) -> FastAPI:
    """Build the gateway application.

    Args:
        secret: HMAC secret used to verify bearer tokens.
        upstreams: First path segment to upstream base URL.
        client: Upstream HTTP client.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(title="API Gateway")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    @app.get("/api/health")
    def health() -> dict[str, str]:
        """Report that the gateway process is up.

        Returns:
            A static status object.
        """
        return {"status": "ok"}

    @app.api_route(
        "/api/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    )
    async def proxy(path: str, request: Request) -> Response:
        """Check the caller and forward the request.

        Args:
            path: Path under ``/api``.
            request: Incoming request.

        Returns:
            The upstream response, or an English error JSON.
        """
        normalized = normalize_path(path)
        if not is_public(normalized):
            header = request.headers.get("authorization")
            if header is None or not header.lower().startswith("bearer "):
                return JSONResponse(
                    status_code=401,
                    content={"error": "unauthorized", "message": "Authentication is required."},
                )
            token = header.split(" ", 1)[1].strip()
            try:
                verify_access_token(token, secret)
            except TokenError as exc:
                return JSONResponse(
                    status_code=401,
                    content={"error": "unauthorized", "message": exc.message},
                )
        base_url = resolve_upstream(normalized, upstreams)
        if base_url is None:
            return JSONResponse(
                status_code=404,
                content={"error": "not_found", "message": "That portal route does not exist."},
            )
        try:
            upstream = await client.forward(
                method=request.method,
                url=f"{base_url.rstrip('/')}/{normalized}",
                query=request.url.query,
                body=await request.body(),
                content_type=request.headers.get("content-type"),
                authorization=request.headers.get("authorization"),
            )
        except httpx.HTTPError:
            return JSONResponse(
                status_code=502,
                content={
                    "error": "upstream_unavailable",
                    "message": "A portal service is unavailable.",
                },
            )
        headers: dict[str, str] = {}
        if upstream.content_type is not None:
            headers["content-type"] = upstream.content_type
        if upstream.content_disposition is not None:
            headers["content-disposition"] = upstream.content_disposition
        return Response(content=upstream.content, status_code=upstream.status_code, headers=headers)

    return app
