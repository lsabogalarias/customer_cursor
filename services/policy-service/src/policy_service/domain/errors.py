"""Domain errors for policies, documents, and claims."""


class PolicyError(Exception):
    """Base class for policy use-case failures."""

    code: str = "policy_error"

    def __init__(self, message: str) -> None:
        """Store an English explanation.

        Args:
            message: Text the HTTP adapter returns to the client.
        """
        super().__init__(message)
        self.message = message


class InvalidPolicyNumber(PolicyError):
    """The policy number does not use the AUTO- or HOME- format."""

    code = "invalid_policy_number"


class PolicyNotFound(PolicyError):
    """The policy does not exist for this customer."""

    code = "policy_not_found"


class VehiclesNotAllowed(PolicyError):
    """Vehicles cannot be changed on a home policy."""

    code = "vehicles_not_allowed"


class DriversNotAllowed(PolicyError):
    """Drivers cannot be changed on a home policy."""

    code = "drivers_not_allowed"


class InvalidVehicle(PolicyError):
    """The vehicle details are incomplete."""

    code = "invalid_vehicle"


class InvalidDriver(PolicyError):
    """The driver details are incomplete."""

    code = "invalid_driver"


class InvalidClaim(PolicyError):
    """The claim description is missing or too long."""

    code = "invalid_claim"


class VehicleNotFound(PolicyError):
    """The vehicle does not exist on this policy."""

    code = "vehicle_not_found"


class DriverNotFound(PolicyError):
    """The driver does not exist on this policy."""

    code = "driver_not_found"


class DocumentNotFound(PolicyError):
    """The document does not exist for this customer."""

    code = "document_not_found"
