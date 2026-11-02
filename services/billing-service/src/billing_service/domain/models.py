"""Billing domain models."""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class PaymentStatus(StrEnum):
    """Whether a scheduled payment is still due."""

    PAID = "paid"
    PENDING = "pending"


class Payment(BaseModel):
    """One scheduled or completed payment.

    Attributes:
        payment_id: Stable identifier.
        user_id: Owner. Omitted from API responses.
        policy_number: Policy this payment belongs to.
        amount: Amount in dollars.
        status: Paid or pending.
        due_date: Date the payment is due.
        description: English description.
        paid_at: When the mock gateway accepted it, if paid.
        confirmation_id: Mock confirmation id, if paid.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    payment_id: str
    user_id: str
    policy_number: str
    amount: Decimal
    status: PaymentStatus
    due_date: date
    description: str
    paid_at: datetime | None
    confirmation_id: str | None
