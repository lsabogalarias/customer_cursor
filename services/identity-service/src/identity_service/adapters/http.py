"""HTTP adapter for the identity service."""

from collections.abc import Callable

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from portal_common.identity import AuthContext
from pydantic import BaseModel, ConfigDict
from starlette.requests import Request

from identity_service.domain.errors import IdentityError
from identity_service.domain.models import LoginCommand, RegisterCommand
from identity_service.domain.use_cases import GetCurrentUser, LoginUser, RegisterUser

_STATUS: dict[str, int] = {
    "invalid_email": 400,
    "weak_password": 400,
    "invalid_name": 400,
    "email_already_registered": 409,
    "invalid_credentials": 401,
    "user_not_found": 404,
}


class RegisterBody(BaseModel):
    """JSON body for account registration.

    Attributes:
        email: Address the customer will use to sign in.
        password: Plain password.
        full_name: Name shown in the portal.
    """

    model_config = ConfigDict(extra="forbid")

    email: str
    password: str
    full_name: str


class LoginBody(BaseModel):
    """JSON body for sign-in.

    Attributes:
        email: Account email.
        password: Plain password.
    """

    model_config = ConfigDict(extra="forbid")

    email: str
    password: str


def create_app(
    register_user: RegisterUser,
    login_user: LoginUser,
    get_current_user: GetCurrentUser,
    require_auth: Callable[..., AuthContext],
) -> FastAPI:
    """Build the identity HTTP application.

    Args:
        register_user: Registration use case.
        login_user: Login use case.
        get_current_user: Profile use case.
        require_auth: FastAPI dependency that yields an AuthContext.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(title="Identity Service")

    @app.exception_handler(IdentityError)
    async def handle_identity_error(_request: Request, exc: IdentityError) -> JSONResponse:
        """Map a domain error to a JSON response.

        Args:
            _request: Incoming request. Unused.
            exc: Domain error raised by a use case.

        Returns:
            JSON body with an English message.
        """
        return JSONResponse(
            status_code=_STATUS.get(exc.code, 400),
            content={"error": exc.code, "message": exc.message},
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        """Report that the process is up.

        Returns:
            A static status object.
        """
        return {"status": "ok"}

    @app.post("/auth/register", status_code=201)
    def register(body: RegisterBody) -> dict[str, str]:
        """Register a customer.

        Args:
            body: Registration JSON.

        Returns:
            Public profile fields.
        """
        profile = register_user.execute(
            RegisterCommand(email=body.email, password=body.password, full_name=body.full_name)
        )
        return {
            "user_id": profile.user_id,
            "email": profile.email,
            "full_name": profile.full_name,
        }

    @app.post("/auth/login")
    def login(body: LoginBody) -> dict[str, str | int]:
        """Sign a customer in.

        Args:
            body: Login JSON.

        Returns:
            Bearer token payload.
        """
        token = login_user.execute(LoginCommand(email=body.email, password=body.password))
        return {
            "access_token": token.access_token,
            "token_type": token.token_type,
            "expires_in": token.expires_in,
        }

    @app.get("/auth/me")
    def me(auth: AuthContext = Depends(require_auth)) -> dict[str, str]:
        """Return the signed-in customer.

        Args:
            auth: Verified caller.

        Returns:
            Public profile fields.
        """
        profile = get_current_user.execute(auth)
        return {
            "user_id": profile.user_id,
            "email": profile.email,
            "full_name": profile.full_name,
        }

    return app
