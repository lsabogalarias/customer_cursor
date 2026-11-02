"""Inbound ports describing what callers can ask of identity."""

from typing import Protocol

from portal_common.identity import AuthContext

from identity_service.domain.models import AccessToken, LoginCommand, RegisterCommand, UserProfile


class RegisterUserPort(Protocol):
    """Open a customer account."""

    def execute(self, command: RegisterCommand) -> UserProfile:
        """Register a new customer.

        Args:
            command: Email, password, and full name.

        Returns:
            The public profile of the new customer.
        """
        ...


class LoginUserPort(Protocol):
    """Sign a customer in."""

    def execute(self, command: LoginCommand) -> AccessToken:
        """Exchange credentials for an access token.

        Args:
            command: Email and plain password.

        Returns:
            A short-lived bearer token.
        """
        ...


class GetCurrentUserPort(Protocol):
    """Read the signed-in customer."""

    def execute(self, auth: AuthContext) -> UserProfile:
        """Return the caller's profile.

        Args:
            auth: Identity taken from the verified JWT.

        Returns:
            Public profile of the caller.
        """
        ...
