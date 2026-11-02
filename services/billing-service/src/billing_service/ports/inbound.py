"""Inbound port for listing payments."""

from typing import Protocol

from portal_common.identity import AuthContext

from billing_service.domain.models import Payment


class ListPaymentsPort(Protocol):
    """Ask for the caller's payment history."""

    def execute(self, auth: AuthContext, policy_number: str | None) -> list[Payment]:
        """Return payments, optionally filtered by policy.

        Args:
            auth: Verified caller.
            policy_number: Optional policy number.

        Returns:
            Payments owned by the caller.
        """
        ...
