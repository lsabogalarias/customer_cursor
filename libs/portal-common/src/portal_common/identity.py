"""Verified caller identity shared by every portal service."""

from pydantic import BaseModel, ConfigDict


class AuthContext(BaseModel):
    """Caller identity taken from a verified JSON Web Token.

    Attributes:
        user_id: Stable customer identifier from the ``sub`` claim.
        email: Customer email carried in the token.
        token: Raw bearer token, forwarded to downstream services.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    user_id: str
    email: str
    token: str
