"""Argon2 password hashing adapter."""

from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError


class Argon2PasswordHasher:
    """Hashes and checks passwords with Argon2id."""

    def __init__(self) -> None:
        """Create a hasher with library defaults."""
        self._hasher = Argon2Hasher()

    def hash_password(self, password: str) -> str:
        """Hash a plain password.

        Args:
            password: Password supplied by the customer.

        Returns:
            Argon2 hash string.
        """
        return self._hasher.hash(password)

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Check a plain password against a stored hash.

        Args:
            password: Password supplied by the customer.
            password_hash: Hash loaded from the account store.

        Returns:
            True when the password matches the hash.
        """
        try:
            return bool(self._hasher.verify(password_hash, password))
        except (InvalidHashError, VerificationError, VerifyMismatchError):
            return False
