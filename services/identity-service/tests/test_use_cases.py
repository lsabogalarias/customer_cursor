"""Use-case tests for registration and login."""

from portal_common.identity import AuthContext

from identity_service.domain.errors import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    InvalidEmail,
    UserNotFound,
    WeakPassword,
)
from identity_service.domain.models import LoginCommand, RegisterCommand, StoredUser
from identity_service.domain.use_cases import GetCurrentUser, LoginUser, RegisterUser
from tests.fakes import FakePasswordHasher, FakeTokenIssuer, FakeUserRepository


def _register() -> tuple[RegisterUser, FakeUserRepository, FakePasswordHasher]:
    """Build a registration use case with fakes.

    Returns:
        The use case, the repository, and the hasher.
    """
    users = FakeUserRepository()
    hasher = FakePasswordHasher()
    return RegisterUser(users, hasher), users, hasher


def test_register_stores_a_hash_and_hides_it_from_the_profile() -> None:
    """A new account keeps the hash in storage and returns only the profile."""
    use_case, users, _hasher = _register()
    profile = use_case.execute(
        RegisterCommand(
            email="New.User@Example.com",
            password="Secret123",
            full_name="New User",
        )
    )
    assert profile.email == "new.user@example.com"
    assert profile.full_name == "New User"
    stored = users.users[profile.user_id]
    assert stored.password_hash == "hash:Secret123"
    assert "password" not in profile.model_dump()


def test_register_rejects_a_duplicate_email() -> None:
    """The same email cannot be registered twice."""
    use_case, _users, _hasher = _register()
    command = RegisterCommand(email="a@example.com", password="Secret123", full_name="Ada")
    use_case.execute(command)
    try:
        use_case.execute(command)
    except EmailAlreadyRegistered as exc:
        assert exc.code == "email_already_registered"
    else:
        raise AssertionError("duplicate email was accepted")


def test_register_rejects_a_weak_password_and_a_bad_email() -> None:
    """Password policy and email shape are enforced in the use case."""
    use_case, _users, _hasher = _register()
    try:
        use_case.execute(
            RegisterCommand(email="a@example.com", password="short", full_name="Ada")
        )
    except WeakPassword:
        pass
    else:
        raise AssertionError("weak password was accepted")
    try:
        use_case.execute(
            RegisterCommand(email="not-an-email", password="Secret123", full_name="Ada")
        )
    except InvalidEmail:
        pass
    else:
        raise AssertionError("invalid email was accepted")


def test_login_returns_a_token_and_hides_which_check_failed() -> None:
    """A matching password returns a token. Unknown and wrong passwords match."""
    users = FakeUserRepository()
    hasher = FakePasswordHasher()
    users.add(
        StoredUser(
            user_id="user-1",
            email="a@example.com",
            full_name="Ada",
            password_hash=hasher.hash_password("Secret123"),
        )
    )
    login = LoginUser(users, hasher, FakeTokenIssuer(), 3600)
    token = login.execute(LoginCommand(email="A@Example.com", password="Secret123"))
    assert token.access_token == "token:user-1:a@example.com"
    assert token.token_type == "bearer"
    assert token.expires_in == 3600
    for command in (
        LoginCommand(email="missing@example.com", password="Secret123"),
        LoginCommand(email="a@example.com", password="Wrong1234"),
    ):
        try:
            login.execute(command)
        except InvalidCredentials as exc:
            assert exc.message == "Invalid email or password."
        else:
            raise AssertionError("invalid credentials were accepted")


def test_current_user_is_limited_to_the_token_subject() -> None:
    """The profile query uses the verified user id and ignores other accounts."""
    users = FakeUserRepository()
    users.add(
        StoredUser(
            user_id="user-1",
            email="a@example.com",
            full_name="Ada",
            password_hash="hash:Secret123",
        )
    )
    current = GetCurrentUser(users)
    profile = current.execute(
        AuthContext(user_id="user-1", email="a@example.com", token="token")
    )
    assert profile.full_name == "Ada"
    try:
        current.execute(AuthContext(user_id="other", email="a@example.com", token="token"))
    except UserNotFound:
        pass
    else:
        raise AssertionError("another user's profile was returned")
