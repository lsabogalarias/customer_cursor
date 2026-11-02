"""HTTP adapter for the billing service."""

from collections.abc import Callable

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from portal_common.identity import AuthContext
from starlette.requests import Request

from billing_service.adapters.present import payment_json
from billing_service.domain.errors import BillingError
from billing_service.domain.use_cases import ListPayments, PayPending

_STATUS: dict[str, int] = {
    "payment_not_found": 404,
    "payment_already_settled": 409,
    "invalid_policy_number": 400,
}


def create_app(
    list_payments: ListPayments,
    pay_pending: PayPending,
    require_auth: Callable[..., AuthContext],
) -> FastAPI:
    """Build the billing HTTP application.

    Args:
        list_payments: History use case.
        pay_pending: Mock pay use case.
        require_auth: FastAPI dependency that yields an AuthContext.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(title="Billing Service")

    @app.exception_handler(BillingError)
    async def handle_billing_error(_request: Request, exc: BillingError) -> JSONResponse:
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

    @app.get("/payments")
    def payments(
        auth: AuthContext = Depends(require_auth),
        policy_number: str | None = None,
    ) -> dict[str, object]:
        """List payments.

        Args:
            auth: Verified caller.
            policy_number: Optional policy filter.

        Returns:
            A payments array.
        """
        found = list_payments.execute(auth, policy_number)
        return {"payments": [payment_json(item) for item in found]}

    @app.post("/payments/{payment_id}/pay")
    def pay(payment_id: str, auth: AuthContext = Depends(require_auth)) -> dict[str, object]:
        """Pay a pending item through the mock gateway.

        Args:
            payment_id: Payment identifier.
            auth: Verified caller.

        Returns:
            The updated payment.
        """
        return payment_json(pay_pending.execute(auth, payment_id))

    return app
