"""Billing domain errors."""


class BillingError(Exception):
    """Base class for billing use-case failures."""

    code: str = "billing_error"

    def __init__(self, message: str) -> None:
        """Store an English explanation.

        Args:
            message: Text the HTTP adapter returns to the client.
        """
        super().__init__(message)
        self.message = message


class PaymentNotFound(BillingError):
    """The payment does not exist for this customer."""

    code = "payment_not_found"


class PaymentAlreadySettled(BillingError):
    """The payment is not waiting to be paid."""

    code = "payment_already_settled"


class InvalidPolicyNumber(BillingError):
    """The optional policy filter is not AUTO-XXXX or HOME-XXXX."""

    code = "invalid_policy_number"
