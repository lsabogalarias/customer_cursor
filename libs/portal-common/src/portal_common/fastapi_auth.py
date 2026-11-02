"""FastAPI dependency that verifies the Authorization header."""

from collections.abc import Callable

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from portal_common.errors import TokenError
from portal_common.identity import AuthContext
from portal_common.tokens import verify_access_token

_bearer = HTTPBearer(auto_error=False)


def build_require_auth(secret: str) -> Callable[..., AuthContext]:
    """Build a FastAPI dependency that returns the verified caller.

    Args:
        secret: HMAC secret shared with the identity service.

    Returns:
        A dependency FastAPI injects as ``Depends(require_auth)``.
    """

    def require_auth(
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    ) -> AuthContext:
        """Read and verify the bearer token on the current request.

        Args:
            credentials: Parsed Authorization header, or None when it is absent.

        Returns:
            The verified AuthContext.

        Raises:
            HTTPException: 401 when the header is missing or the token is invalid.
        """
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "unauthorized",
                    "message": "Authentication is required.",
                },
            )
        try:
            return verify_access_token(credentials.credentials, secret)
        except TokenError as exc:
            raise HTTPException(
                status_code=401,
                detail={"error": "unauthorized", "message": exc.message},
            ) from exc

    return require_auth
