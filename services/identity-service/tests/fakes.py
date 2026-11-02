"""In-memory fakes for identity use-case tests."""

from portal_common.identity import AuthContext

from identity_service.domain.models import StoredUser


class FakeUserRepository:
    """Stores accounts in a dictionary."""

    def __init__(self) -> None:
        """Start with an empty account set."""
        self.users: dict[str, StoredUser] = {}

    def find_by_email(self, email: str) -> StoredUser | None:
        """Load an account by normalized email.

        Args:
            email: Normalized email address.

        Returns:
            The stored account, or None when the address is unknown.
        """
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    def add(self, user: StoredUser) -> None:
        """Insert a new account.

        Args:
            user: Account to persist, including the password hash.
        """
        self.users[user.user_id] = user

    def find_by_id(self, auth: AuthContext) -> StoredUser | None:
        """Load the account that belongs to the verified caller.

        Args:
            auth: Identity taken from the verified JWT.

        Returns:
            The caller's account, or None when it does not exist.
        """
        return self.users.get(auth.user_id)


class FakePasswordHasher:
    """Reversible stand-in so tests do not depend on Argon2."""

    def hash_password(self, password: str) -> str:
        """Hash a plain password.

        Args:
            password: Password supplied by the customer.

        Returns:
            A prefixed stand-in hash.
        """
        return f"hash:{password}"

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Check a plain password against a stored hash.

        Args:
            password: Password supplied by the customer.
            password_hash: Hash loaded from the account store.

        Returns:
            True when the password matches the stand-in hash.
        """
        return password_hash == f"hash:{password}"


class FakeTokenIssuer:
    """Issues deterministic tokens."""

    def issue(self, user_id: str, email: str) -> str:
        """Sign an access token for a customer.

        Args:
            user_id: Customer identifier.
            email: Customer email.

        Returns:
            A deterministic token string.
        """
        return f"token:{user_id}:{email}"
