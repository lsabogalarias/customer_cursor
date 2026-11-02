"""Issue and verify HMAC JSON Web Tokens.

This module is an adapter. Domain use cases must not import it. The identity
service wraps ``issue_access_token`` behind a port.
"""

from datetime import UTC, datetime, timedelta
from typing import Final

import jwt

from portal_common.errors import TokenError
from portal_common.identity import AuthContext

_ALGORITHM: Final[str] = "HS256"


def issue_access_token(*, user_id: str, email: str, secret: str, ttl_seconds: int) -> str:
    """Sign a short-lived access token.

    Args:
        user_id: Customer identifier stored in the ``sub`` claim.
        email: Customer email stored in the ``email`` claim.
        secret: HMAC secret. The local default is a demo placeholder.
        ttl_seconds: Lifetime of the token in seconds.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
    }
    encoded = jwt.encode(payload, secret, algorithm=_ALGORITHM)
    if isinstance(encoded, bytes):
        return encoded.decode("ascii")
    return str(encoded)


def verify_access_token(token: str, secret: str) -> AuthContext:
    """Validate a bearer token and build an AuthContext.

    Args:
        token: Raw JWT, without the ``Bearer`` prefix.
        secret: HMAC secret used when the token was issued.

    Returns:
        AuthContext containing the caller id, email, and the same token.

    Raises:
        TokenError: The token is expired, malformed, or missing required claims.
    """
    try:
        decoded: object = jwt.decode(token, secret, algorithms=[_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise TokenError("Invalid or expired access token.") from exc
    if not isinstance(decoded, dict):
        raise TokenError("Access token payload is not an object.")
    user_id = decoded.get("sub")
    email = decoded.get("email")
    if not isinstance(user_id, str) or not user_id:
        raise TokenError("Access token is missing required claims.")
    if not isinstance(email, str) or not email:
        raise TokenError("Access token is missing required claims.")
    return AuthContext(user_id=user_id, email=email, token=token)
