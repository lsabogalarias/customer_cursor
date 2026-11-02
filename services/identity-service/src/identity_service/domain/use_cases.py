"""Use cases for registration, login, and the current profile."""

import re
from uuid import uuid4

from portal_common.identity import AuthContext

from identity_service.domain.errors import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    InvalidEmail,
    InvalidName,
    UserNotFound,
    WeakPassword,
)
from identity_service.domain.models import (
    AccessToken,
    LoginCommand,
    RegisterCommand,
    StoredUser,
    UserProfile,
)
from identity_service.ports.outbound import PasswordHasher, TokenIssuer, UserRepository

_EMAIL = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


def _normalize_email(email: str) -> str:
    """Trim and lowercase an email address.

    Args:
        email: Raw address from the client.

    Returns:
        Normalized address.

    Raises:
        InvalidEmail: The address does not match the accepted shape.
    """
    normalized = email.strip().lower()
    if _EMAIL.fullmatch(normalized) is None:
        raise InvalidEmail("Enter a valid email address.")
    return normalized


def _check_password(password: str) -> None:
    """Reject passwords that are too short or lack a letter and a digit.

    Args:
        password: Plain password from the client.

    Raises:
        WeakPassword: The password does not meet the policy.
    """
    has_letter = any(character.isalpha() for character in password)
    has_digit = any(character.isdigit() for character in password)
    if len(password) < 8 or not has_letter or not has_digit:
        raise WeakPassword("Use at least 8 characters with a letter and a digit.")


def _profile(user: StoredUser) -> UserProfile:
    """Drop the password hash from a stored account.

    Args:
        user: Account loaded from the repository.

    Returns:
        Public profile.
    """
    return UserProfile(user_id=user.user_id, email=user.email, full_name=user.full_name)


class RegisterUser:
    """Create a customer account."""

    def __init__(self, users: UserRepository, hasher: PasswordHasher) -> None:
        """Store the ports this use case needs.

        Args:
            users: Account repository.
            hasher: Password hashing port.
        """
        self._users = users
        self._hasher = hasher

    def execute(self, command: RegisterCommand) -> UserProfile:
        """Register a new customer.

        Args:
            command: Email, password, and full name.

        Returns:
            The public profile of the new customer.

        Raises:
            InvalidEmail: The email address is not usable.
            InvalidName: The name is missing.
            WeakPassword: The password does not meet the policy.
            EmailAlreadyRegistered: The email is already in use.
        """
        email = _normalize_email(command.email)
        full_name = command.full_name.strip()
        if len(full_name) < 2:
            raise InvalidName("Enter the customer name.")
        _check_password(command.password)
        if self._users.find_by_email(email) is not None:
            raise EmailAlreadyRegistered("An account with this email already exists.")
        user = StoredUser(
            user_id=str(uuid4()),
            email=email,
            full_name=full_name,
            password_hash=self._hasher.hash_password(command.password),
        )
        self._users.add(user)
        return _profile(user)


class LoginUser:
    """Exchange an email and password for an access token."""

    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        tokens: TokenIssuer,
        ttl_seconds: int,
    ) -> None:
        """Store the ports this use case needs.

        Args:
            users: Account repository.
            hasher: Password hashing port.
            tokens: Token issuer port.
            ttl_seconds: Lifetime advertised on the access token.
        """
        self._users = users
        self._hasher = hasher
        self._tokens = tokens
        self._ttl_seconds = ttl_seconds

    def execute(self, command: LoginCommand) -> AccessToken:
        """Sign the customer in.

        Unknown emails and wrong passwords return the same error so the
        response does not reveal which accounts exist.

        Args:
            command: Email and plain password.

        Returns:
            A short-lived bearer token.

        Raises:
            InvalidCredentials: The email and password do not match.
        """
        email = command.email.strip().lower()
        user = self._users.find_by_email(email)
        if user is None or not self._hasher.verify_password(command.password, user.password_hash):
            raise InvalidCredentials("Invalid email or password.")
        return AccessToken(
            access_token=self._tokens.issue(user.user_id, user.email),
            token_type="bearer",
            expires_in=self._ttl_seconds,
        )


class GetCurrentUser:
    """Load the profile for the customer named by the verified token."""

    def __init__(self, users: UserRepository) -> None:
        """Store the account repository.

        Args:
            users: Account repository.
        """
        self._users = users

    def execute(self, auth: AuthContext) -> UserProfile:
        """Return the caller's profile.

        Args:
            auth: Identity taken from the verified JWT.

        Returns:
            Public profile of the caller.

        Raises:
            UserNotFound: No account matches the token subject.
        """
        user = self._users.find_by_id(auth)
        if user is None:
            raise UserNotFound("Customer account was not found.")
        return _profile(user)
