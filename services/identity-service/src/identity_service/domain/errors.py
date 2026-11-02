"""Domain errors for registration and login."""


class IdentityError(Exception):
    """Base class for identity use-case failures."""

    code: str = "identity_error"

    def __init__(self, message: str) -> None:
        """Store an English explanation.

        Args:
            message: Text the HTTP adapter returns to the client.
        """
        super().__init__(message)
        self.message = message


class InvalidEmail(IdentityError):
    """The email address is not usable."""

    code = "invalid_email"


class WeakPassword(IdentityError):
    """The password does not meet the local policy."""

    code = "weak_password"


class InvalidName(IdentityError):
    """The customer name is empty or too short."""

    code = "invalid_name"


class EmailAlreadyRegistered(IdentityError):
    """An account already exists for this email address."""

    code = "email_already_registered"


class InvalidCredentials(IdentityError):
    """The email and password do not match an account."""

    code = "invalid_credentials"


class UserNotFound(IdentityError):
    """The verified token does not match a stored customer."""

    code = "user_not_found"
