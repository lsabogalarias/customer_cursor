"""JWT issuer adapter."""

from portal_common.tokens import issue_access_token


class JwtTokenIssuer:
    """Signs access tokens with the shared HMAC secret."""

    def __init__(self, secret: str, ttl_seconds: int) -> None:
        """Store the signing settings.

        Args:
            secret: HMAC secret read from the environment in ``main``.
            ttl_seconds: Token lifetime in seconds.
        """
        self._secret = secret
        self._ttl_seconds = ttl_seconds

    def issue(self, user_id: str, email: str) -> str:
        """Sign an access token for a customer.

        Args:
            user_id: Customer identifier.
            email: Customer email.

        Returns:
            Encoded JWT.
        """
        return issue_access_token(
            user_id=user_id,
            email=email,
            secret=self._secret,
            ttl_seconds=self._ttl_seconds,
        )
