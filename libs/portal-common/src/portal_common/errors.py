"""Errors raised by shared adapter helpers."""


class TokenError(Exception):
    """Raised when a bearer token is missing, expired, or invalid."""

    def __init__(self, message: str) -> None:
        """Store an English explanation.

        Args:
            message: Text safe to return to an API client.
        """
        super().__init__(message)
        self.message = message
