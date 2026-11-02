"""Use-case tests for payments."""

from datetime import date
from decimal import Decimal

from portal_common.identity import AuthContext

from billing_service.domain.errors import PaymentAlreadySettled, PaymentNotFound
from billing_service.domain.models import Payment, PaymentStatus
from billing_service.domain.use_cases import ListPayments, PayPending
from billing_service.ports.outbound import PaymentGateway


class FakePayments:
    """In-memory payments filtered by caller."""

    def __init__(self) -> None:
        """Start empty."""
        self.rows: list[Payment] = []

    def list_payments(self, auth: AuthContext, policy_number: str | None) -> list[Payment]:
        """List owned payments.

        Args:
            auth: Verified caller.
            policy_number: Optional filter.

        Returns:
            Matching payments.
        """
        found = [item for item in self.rows if item.user_id == auth.user_id]
        if policy_number is None:
            return found
        return [item for item in found if item.policy_number == policy_number]

    def get_payment(self, auth: AuthContext, payment_id: str) -> Payment | None:
        """Load an owned payment.

        Args:
            auth: Verified caller.
            payment_id: Payment identifier.

        Returns:
            The payment, or None.
        """
        for item in self.rows:
            if item.user_id == auth.user_id and item.payment_id == payment_id:
                return item
        return None

    def mark_paid(
        self,
        auth: AuthContext,
        payment_id: str,
        paid_at: object,
        confirmation_id: str,
    ) -> Payment | None:
        """Mark an owned pending payment paid.

        Args:
            auth: Verified caller.
            payment_id: Payment identifier.
            paid_at: Timestamp. Tests pass a datetime.
            confirmation_id: Mock confirmation id.

        Returns:
            The updated payment, or None.
        """
        from datetime import datetime

        if not isinstance(paid_at, datetime):
            raise AssertionError("paid_at must be a datetime")
        for index, item in enumerate(self.rows):
            if (
                item.user_id == auth.user_id
                and item.payment_id == payment_id
                and item.status is PaymentStatus.PENDING
            ):
                updated = item.model_copy(
                    update={
                        "status": PaymentStatus.PAID,
                        "paid_at": paid_at,
                        "confirmation_id": confirmation_id,
                    }
                )
                self.rows[index] = updated
                return updated
        return None


class FakeGateway:
    """Records charges and returns a fixed confirmation id."""

    def __init__(self) -> None:
        """Start with an empty log."""
        self.charges: list[tuple[str, str, Decimal]] = []

    def charge(self, auth: AuthContext, payment_id: str, amount: Decimal) -> str:
        """Record a mock charge.

        Args:
            auth: Verified caller.
            payment_id: Payment identifier.
            amount: Amount in dollars.

        Returns:
            A fixed confirmation id.
        """
        self.charges.append((auth.user_id, payment_id, amount))
        return "mock-confirm"


def _payment(payment_id: str, user_id: str, status: PaymentStatus) -> Payment:
    """Build a payment fixture.

    Args:
        payment_id: Payment identifier.
        user_id: Owner.
        status: Paid or pending.

    Returns:
        A payment for AUTO-1001.
    """
    return Payment(
        payment_id=payment_id,
        user_id=user_id,
        policy_number="AUTO-1001",
        amount=Decimal("640.00"),
        status=status,
        due_date=date(2026, 12, 1),
        description="Installment",
        paid_at=None,
        confirmation_id=None,
    )


def test_pay_pending_records_a_mock_confirmation_and_hides_other_customers() -> None:
    """Paying updates only the caller's pending row."""
    store = FakePayments()
    store.rows.extend(
        [
            _payment("pay-1", "user-1", PaymentStatus.PENDING),
            _payment("pay-2", "user-2", PaymentStatus.PENDING),
            _payment("pay-3", "user-1", PaymentStatus.PAID),
        ]
    )
    gateway: PaymentGateway = FakeGateway()
    auth = AuthContext(user_id="user-1", email="a@example.com", token="token")
    paid = PayPending(store, gateway).execute(auth, "pay-1")
    assert paid.status is PaymentStatus.PAID
    assert paid.confirmation_id == "mock-confirm"
    assert isinstance(gateway, FakeGateway)
    assert gateway.charges == [("user-1", "pay-1", Decimal("640.00"))]
    visible = ListPayments(store).execute(auth, None)
    assert {item.payment_id for item in visible} == {"pay-1", "pay-3"}
    try:
        PayPending(store, gateway).execute(auth, "pay-2")
    except PaymentNotFound:
        pass
    else:
        raise AssertionError("another customer's payment was charged")
    try:
        PayPending(store, gateway).execute(auth, "pay-3")
    except PaymentAlreadySettled:
        pass
    else:
        raise AssertionError("a paid item was charged again")
