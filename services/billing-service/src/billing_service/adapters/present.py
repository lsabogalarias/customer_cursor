"""JSON shapes for billing HTTP responses."""

from decimal import Decimal

from billing_service.domain.models import Payment


def money(value: Decimal) -> str:
    """Format a dollar amount for JSON.

    Args:
        value: Amount in dollars.

    Returns:
        A string with two decimal places.
    """
    return f"{value.quantize(Decimal('0.01')):.2f}"


def payment_json(payment: Payment) -> dict[str, object]:
    """Map a payment to the public JSON object.

    Args:
        payment: Domain payment.

    Returns:
        JSON-ready dictionary without the owner id.
    """
    paid_at = None if payment.paid_at is None else payment.paid_at.isoformat()
    return {
        "payment_id": payment.payment_id,
        "policy_number": payment.policy_number,
        "amount": money(payment.amount),
        "status": payment.status.value,
        "due_date": payment.due_date.isoformat(),
        "description": payment.description,
        "paid_at": paid_at,
        "confirmation_id": payment.confirmation_id,
    }
