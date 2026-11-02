"""Outbound ports for billing."""

from datetime import datetime
from decimal import Decimal
from typing import Protocol

from portal_common.identity import AuthContext

from billing_service.domain.models import Payment


class PaymentRepository(Protocol):
    """Customer-scoped payment storage."""

    def list_payments(self, auth: AuthContext, policy_number: str | None) -> list[Payment]:
        """List payments for the caller.

        Args:
            auth: Verified caller.
            policy_number: Optional policy filter.

        Returns:
            Payments owned by the caller.
        """
        ...

    def get_payment(self, auth: AuthContext, payment_id: str) -> Payment | None:
        """Load one payment when the caller owns it.

        Args:
            auth: Verified caller.
            payment_id: Payment identifier.

        Returns:
            The payment, or None.
        """
        ...

    def mark_paid(
        self,
        auth: AuthContext,
        payment_id: str,
        paid_at: datetime,
        confirmation_id: str,
    ) -> Payment | None:
        """Mark a pending payment paid when the caller owns it.

        Args:
            auth: Verified caller.
            payment_id: Payment identifier.
            paid_at: Timestamp recorded for the mock charge.
            confirmation_id: Confirmation id from the mock gateway.

        Returns:
            The updated payment, or None when it is not an owned pending row.
        """
        ...


class PaymentGateway(Protocol):
    """Charges a pending payment. The POC implementation never leaves the process."""

    def charge(self, auth: AuthContext, payment_id: str, amount: Decimal) -> str:
        """Record a mock charge and return a confirmation id.

        Args:
            auth: Verified caller.
            payment_id: Payment being charged.
            amount: Amount in dollars.

        Returns:
            A fake confirmation id. No network call is made.
        """
        ...
