"""JSON shapes for policy HTTP responses."""

from decimal import Decimal

from policy_service.domain.models import (
    Claim,
    DocumentSummary,
    Driver,
    IdCard,
    Policy,
    RenewalQuote,
    Vehicle,
)


def money(value: Decimal) -> str:
    """Format a dollar amount for JSON.

    Args:
        value: Amount in dollars.

    Returns:
        A string with two decimal places.
    """
    return f"{value.quantize(Decimal('0.01')):.2f}"


def policy_json(policy: Policy) -> dict[str, object]:
    """Map a policy to the public JSON object.

    Args:
        policy: Domain policy.

    Returns:
        JSON-ready dictionary without the owner id.
    """
    return {
        "policy_number": policy.policy_number,
        "line_of_business": policy.line_of_business.value,
        "product_name": policy.product_name,
        "status": policy.status.value,
        "insured_name": policy.insured_name,
        "property_address": policy.property_address,
        "effective_date": policy.effective_date.isoformat(),
        "expiration_date": policy.expiration_date.isoformat(),
        "premium": money(policy.premium),
    }


def vehicle_json(vehicle: Vehicle) -> dict[str, object]:
    """Map a vehicle to JSON.

    Args:
        vehicle: Domain vehicle.

    Returns:
        JSON-ready dictionary.
    """
    return {
        "vehicle_id": vehicle.vehicle_id,
        "policy_number": vehicle.policy_number,
        "year": vehicle.year,
        "make": vehicle.make,
        "model": vehicle.model,
        "vin": vehicle.vin,
    }


def driver_json(driver: Driver) -> dict[str, object]:
    """Map a driver to JSON.

    Args:
        driver: Domain driver.

    Returns:
        JSON-ready dictionary.
    """
    return {
        "driver_id": driver.driver_id,
        "policy_number": driver.policy_number,
        "full_name": driver.full_name,
        "license_number": driver.license_number,
        "date_of_birth": driver.date_of_birth.isoformat(),
    }


def document_json(document: DocumentSummary) -> dict[str, object]:
    """Map document metadata to JSON.

    Args:
        document: Document summary.

    Returns:
        JSON-ready dictionary without the file body.
    """
    return {
        "document_id": document.document_id,
        "policy_number": document.policy_number,
        "title": document.title,
        "file_name": document.file_name,
        "content_type": document.content_type,
    }


def claim_json(claim: Claim) -> dict[str, object]:
    """Map a claim to JSON.

    Args:
        claim: Domain claim.

    Returns:
        JSON-ready dictionary.
    """
    return {
        "claim_id": claim.claim_id,
        "policy_number": claim.policy_number,
        "description": claim.description,
        "status": claim.status,
        "filed_at": claim.filed_at.isoformat(),
    }


def renewal_json(quote: RenewalQuote) -> dict[str, object]:
    """Map a renewal quote to JSON.

    Args:
        quote: Renewal figures.

    Returns:
        JSON-ready dictionary with string premiums.
    """
    return {
        "policy_number": quote.policy_number,
        "current_premium": money(quote.current_premium),
        "renewal_premium": money(quote.renewal_premium),
        "renewal_effective_date": quote.renewal_effective_date.isoformat(),
        "status": quote.status.value,
    }


def id_card_json(card: IdCard) -> dict[str, object]:
    """Map an ID card to JSON.

    Args:
        card: ID card.

    Returns:
        JSON-ready dictionary.
    """
    return {
        "policy_number": card.policy_number,
        "insured_name": card.insured_name,
        "line_of_business": card.line_of_business.value,
        "effective_date": card.effective_date.isoformat(),
        "expiration_date": card.expiration_date.isoformat(),
        "property_address": card.property_address,
        "vehicles": [vehicle_json(vehicle) for vehicle in card.vehicles],
    }
