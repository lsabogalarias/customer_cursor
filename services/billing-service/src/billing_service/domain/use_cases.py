"""Use cases for payment history and mock payment."""

import re
from datetime import UTC, datetime

from portal_common.identity import AuthContext

from billing_service.domain.errors import (
    InvalidPolicyNumber,
    PaymentAlreadySettled,
    PaymentNotFound,
)
from billing_service.domain.models import Payment, PaymentStatus
from billing_service.ports.outbound import PaymentGateway, PaymentRepository

_NUMBER = re.compile(r"^(AUTO|HOME)-\d{4}$")


class ListPayments:
    """List the caller's payments."""

    def __init__(self, payments: PaymentRepository) -> None:
        """Store the repository.

        Args:
            payments: Payment repository.
        """
        self._payments = payments

    def execute(self, auth: AuthContext, policy_number: str | None) -> list[Payment]:
        """Return payments, optionally filtered by policy.

        Args:
            auth: Verified caller.
            policy_number: Optional policy number.

        Returns:
            Payments owned by the caller.

        Raises:
            InvalidPolicyNumber: The filter is not empty and has the wrong shape.
        """
        number: str | None = None
        if policy_number is not None and policy_number.strip():
            number = policy_number.strip().upper()
            if _NUMBER.fullmatch(number) is None:
                raise InvalidPolicyNumber("Policy numbers look like AUTO-1234 or HOME-1234.")
        return self._payments.list_payments(auth, number)


class PayPending:
    """Charge a pending payment through the mock gateway."""

    def __init__(self, payments: PaymentRepository, gateway: PaymentGateway) -> None:
        """Store the ports.

        Args:
            payments: Payment repository.
            gateway: Mock payment gateway.
        """
        self._payments = payments
        self._gateway = gateway

    def execute(self, auth: AuthContext, payment_id: str) -> Payment:
        """Pay one pending item.

        Args:
            auth: Verified caller.
            payment_id: Payment identifier.

        Returns:
            The payment after the mock charge.

        Raises:
            PaymentNotFound: The caller does not have this payment.
            PaymentAlreadySettled: The payment is already paid.
        """
        payment = self._payments.get_payment(auth, payment_id)
        if payment is None:
            raise PaymentNotFound("Payment was not found.")
        if payment.status is not PaymentStatus.PENDING:
            raise PaymentAlreadySettled("This payment has already been paid.")
        confirmation_id = self._gateway.charge(auth, payment.payment_id, payment.amount)
        saved = self._payments.mark_paid(
            auth,
            payment.payment_id,
            datetime.now(UTC),
            confirmation_id,
        )
        if saved is None:
            raise PaymentNotFound("Payment was not found.")
        return saved
