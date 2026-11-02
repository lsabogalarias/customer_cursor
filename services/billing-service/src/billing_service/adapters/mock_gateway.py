"""In-memory payment gateway. It records the attempt and does not use the network."""

from decimal import Decimal
from uuid import uuid4

from portal_common.identity import AuthContext


class InMemoryPaymentGateway:
    """Mock card gateway used by the POC."""

    def __init__(self) -> None:
        """Start with an empty charge log."""
        self.charges: list[tuple[str, str, Decimal]] = []

    def charge(self, auth: AuthContext, payment_id: str, amount: Decimal) -> str:
        """Record a mock charge and return a confirmation id.

        Args:
            auth: Verified caller.
            payment_id: Payment being charged.
            amount: Amount in dollars.

        Returns:
            A fake confirmation id.
        """
        self.charges.append((auth.user_id, payment_id, amount))
        return f"mock-{uuid4().hex[:12]}"
