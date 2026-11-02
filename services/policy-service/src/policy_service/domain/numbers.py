"""Policy number rules shared by policy use cases."""

import re

from policy_service.domain.errors import InvalidPolicyNumber

_NUMBER = re.compile(r"^(AUTO|HOME)-\d{4}$")


def parse_policy_number(value: str) -> str:
    """Normalize and validate a policy number.

    Args:
        value: Raw policy number from the client.

    Returns:
        Uppercase policy number.

    Raises:
        InvalidPolicyNumber: The value is not ``AUTO-XXXX`` or ``HOME-XXXX``.
    """
    normalized = value.strip().upper()
    if _NUMBER.fullmatch(normalized) is None:
        raise InvalidPolicyNumber("Policy numbers look like AUTO-1234 or HOME-1234.")
    return normalized
