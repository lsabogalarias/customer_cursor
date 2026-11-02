"""Identity domain models."""

from pydantic import BaseModel, ConfigDict


class RegisterCommand(BaseModel):
    """Data required to open a customer account.

    Attributes:
        email: Address the customer will use to sign in.
        password: Plain password. It is hashed before persistence.
        full_name: Name shown in the portal.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    email: str
    password: str
    full_name: str


class LoginCommand(BaseModel):
    """Data required to sign in.

    Attributes:
        email: Account email.
        password: Plain password to check against the stored hash.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    email: str
    password: str


class UserProfile(BaseModel):
    """Public customer profile. The password hash is never included.

    Attributes:
        user_id: Stable customer identifier.
        email: Normalized email address.
        full_name: Display name.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    user_id: str
    email: str
    full_name: str


class StoredUser(BaseModel):
    """Persisted account, including the password hash.

    Attributes:
        user_id: Stable customer identifier.
        email: Normalized email address.
        full_name: Display name.
        password_hash: Argon2 hash. Never returned by an API.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    user_id: str
    email: str
    full_name: str
    password_hash: str


class AccessToken(BaseModel):
    """Signed token returned after a successful login.

    Attributes:
        access_token: Encoded JWT.
        token_type: Always ``bearer``.
        expires_in: Lifetime in seconds.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    access_token: str
    token_type: str
    expires_in: int
