"""Outbound ports for the identity service."""

from typing import Protocol

from portal_common.identity import AuthContext

from identity_service.domain.models import StoredUser


class UserRepository(Protocol):
    """Account storage.

    ``find_by_email`` and ``add`` run before a JWT exists. They are the
    authentication boundary. ``find_by_id`` reads a customer record and
    therefore requires AuthContext.
    """

    def find_by_email(self, email: str) -> StoredUser | None:
        """Load an account by normalized email.

        Args:
            email: Normalized email address.

        Returns:
            The stored account, or None when the address is unknown.
        """
        ...

    def add(self, user: StoredUser) -> None:
        """Insert a new account.

        Args:
            user: Account to persist, including the password hash.
        """
        ...

    def find_by_id(self, auth: AuthContext) -> StoredUser | None:
        """Load the account that belongs to the verified caller.

        Args:
            auth: Identity taken from the verified JWT.

        Returns:
            The caller's account, or None when it does not exist.
        """
        ...


class PasswordHasher(Protocol):
    """One-way password hashing."""

    def hash_password(self, password: str) -> str:
        """Hash a plain password.

        Args:
            password: Password supplied by the customer.

        Returns:
            A stored hash. The plain password is not recoverable.
        """
        ...

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Check a plain password against a stored hash.

        Args:
            password: Password supplied by the customer.
            password_hash: Hash loaded from the account store.

        Returns:
            True when the password matches the hash.
        """
        ...


class TokenIssuer(Protocol):
    """Creates access tokens. Verification lives at each service edge."""

    def issue(self, user_id: str, email: str) -> str:
        """Sign an access token for a customer.

        Args:
            user_id: Customer identifier.
            email: Customer email.

        Returns:
            Encoded JWT.
        """
        ...
