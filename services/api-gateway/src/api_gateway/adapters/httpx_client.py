"""httpx adapter. This is the only module that speaks HTTP to other services."""

import httpx

from api_gateway.ports.outbound import UpstreamResponse


class HttpxUpstreamClient:
    """Forwards requests with a short timeout."""

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        """Store the timeout.

        Args:
            timeout_seconds: Per-request timeout.
        """
        self._timeout_seconds = timeout_seconds

    async def forward(
        self,
        *,
        method: str,
        url: str,
        query: str,
        body: bytes,
        content_type: str | None,
        authorization: str | None,
    ) -> UpstreamResponse:
        """Forward one request.

        Args:
            method: HTTP method.
            url: Absolute URL without the query string.
            query: Raw query string, without ``?``.
            body: Raw body.
            content_type: Content-Type header, if present.
            authorization: Authorization header, if present.

        Returns:
            Status, body, and selected response headers.

        Raises:
            httpx.HTTPError: The upstream could not be reached.
        """
        headers: dict[str, str] = {}
        if content_type is not None:
            headers["content-type"] = content_type
        if authorization is not None:
            headers["authorization"] = authorization
        target = url if not query else f"{url}?{query}"
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.request(method, target, content=body, headers=headers)
        return UpstreamResponse(
            status_code=response.status_code,
            content=response.content,
            content_type=response.headers.get("content-type"),
            content_disposition=response.headers.get("content-disposition"),
        )
