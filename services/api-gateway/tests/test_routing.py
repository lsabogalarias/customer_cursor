"""Routing tests for the gateway."""

from fastapi.testclient import TestClient

from api_gateway.adapters.http import create_app
from api_gateway.domain.routing import is_public, resolve_upstream
from api_gateway.ports.outbound import UpstreamResponse


class RejectingClient:
    """Upstream stand-in that fails the test if the gateway calls it."""

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
        """Refuse to forward.

        Args:
            method: HTTP method.
            url: Absolute URL.
            query: Query string.
            body: Raw body.
            content_type: Content-Type header.
            authorization: Authorization header.

        Returns:
            This method does not return.

        Raises:
            AssertionError: The gateway forwarded a request that should have stopped.
        """
        del method, url, query, body, content_type, authorization
        raise AssertionError("upstream was called")


def test_public_paths_and_upstream_selection() -> None:
    """Login is public. Policies and documents share the policy service."""
    upstreams = {
        "auth": "http://identity",
        "policies": "http://policy",
        "documents": "http://policy",
        "payments": "http://billing",
        "contact": "http://contact",
    }
    assert is_public("auth/login")
    assert is_public("/auth/register/")
    assert not is_public("auth/me")
    assert resolve_upstream("policies/AUTO-1001", upstreams) == "http://policy"
    assert resolve_upstream("documents/doc-1", upstreams) == "http://policy"
    assert resolve_upstream("payments", upstreams) == "http://billing"
    assert resolve_upstream("unknown", upstreams) is None


def test_missing_token_is_rejected_before_the_upstream() -> None:
    """A protected route returns 401 and does not call a service."""
    app = create_app("secret", {"policies": "http://policy"}, RejectingClient())
    response = TestClient(app).get("/api/policies")
    assert response.status_code == 401
    body = response.json()
    assert isinstance(body, dict)
    assert body["error"] == "unauthorized"
