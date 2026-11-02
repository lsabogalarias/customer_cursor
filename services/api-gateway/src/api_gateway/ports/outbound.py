"""Outbound port for calling an upstream service."""

from typing import Protocol

from pydantic import BaseModel, ConfigDict


class UpstreamResponse(BaseModel):
    """Selected fields from an upstream HTTP response.

    Attributes:
        status_code: HTTP status.
        content: Raw body.
        content_type: Content-Type header, if present.
        content_disposition: Content-Disposition header, if present.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    status_code: int
    content: bytes
    content_type: str | None
    content_disposition: str | None


class UpstreamClient(Protocol):
    """Sends a request to one portal service."""

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
            Status, body, and the headers the gateway is allowed to pass back.
        """
        ...
