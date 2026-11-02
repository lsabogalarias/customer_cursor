"""Use cases for policies, documents, renewal, and claims."""

from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import uuid4

from portal_common.identity import AuthContext

from policy_service.domain.errors import (
    DocumentNotFound,
    DriverNotFound,
    DriversNotAllowed,
    InvalidClaim,
    InvalidDriver,
    InvalidVehicle,
    PolicyNotFound,
    VehicleNotFound,
    VehiclesNotAllowed,
)
from policy_service.domain.models import (
    Claim,
    DocumentFile,
    DocumentSummary,
    Driver,
    IdCard,
    NewDriver,
    NewVehicle,
    Policy,
    PolicyStatus,
    RenewalQuote,
    Vehicle,
)
from policy_service.domain.numbers import parse_policy_number
from policy_service.ports.outbound import PolicyRepository


def require_policy(policies: PolicyRepository, auth: AuthContext, policy_number: str) -> Policy:
    """Load a policy the caller owns.

    Args:
        policies: Policy repository.
        auth: Verified caller.
        policy_number: Raw or normalized policy number.

    Returns:
        The owned policy.

    Raises:
        InvalidPolicyNumber: The number format is wrong.
        PolicyNotFound: The caller does not have this policy.
    """
    number = parse_policy_number(policy_number)
    policy = policies.get_policy(auth, number)
    if policy is None:
        raise PolicyNotFound("Policy was not found.")
    return policy


class ListPolicies:
    """List the caller's policies."""

    def __init__(self, policies: PolicyRepository) -> None:
        """Store the repository.

        Args:
            policies: Policy repository.
        """
        self._policies = policies

    def execute(self, auth: AuthContext) -> list[Policy]:
        """Return every policy owned by the caller.

        Args:
            auth: Verified caller.

        Returns:
            The caller's policies.
        """
        return self._policies.list_policies(auth)


class GetPolicy:
    """Load one owned policy."""

    def __init__(self, policies: PolicyRepository) -> None:
        """Store the repository.

        Args:
            policies: Policy repository.
        """
        self._policies = policies

    def execute(self, auth: AuthContext, policy_number: str) -> Policy:
        """Return one policy.

        Args:
            auth: Verified caller.
            policy_number: Policy number.

        Returns:
            The owned policy.
        """
        return require_policy(self._policies, auth, policy_number)


class RenewPolicy:
    """Mark a policy as renewal requested."""

    def __init__(self, policies: PolicyRepository) -> None:
        """Store the repository.

        Args:
            policies: Policy repository.
        """
        self._policies = policies

    def execute(self, auth: AuthContext, policy_number: str) -> Policy:
        """Request renewal. Repeating the call leaves the status unchanged.

        Args:
            auth: Verified caller.
            policy_number: Policy number.

        Returns:
            The policy after the request.
        """
        policy = require_policy(self._policies, auth, policy_number)
        if policy.status is PolicyStatus.RENEWAL_REQUESTED:
            return policy
        updated = self._policies.save_status(
            auth, policy.policy_number, PolicyStatus.RENEWAL_REQUESTED
        )
        if updated is None:
            raise PolicyNotFound("Policy was not found.")
        return updated


class GetRenewalDetails:
    """Build the renewal quote for a policy."""

    def __init__(self, policies: PolicyRepository) -> None:
        """Store the repository.

        Args:
            policies: Policy repository.
        """
        self._policies = policies

    def execute(self, auth: AuthContext, policy_number: str) -> RenewalQuote:
        """Return current and offered premiums.

        The offered premium is five percent above the current term, rounded
        half up to cents. No carrier rating call is made.

        Args:
            auth: Verified caller.
            policy_number: Policy number.

        Returns:
            Renewal figures.
        """
        policy = require_policy(self._policies, auth, policy_number)
        offered = (policy.premium * Decimal("1.05")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return RenewalQuote(
            policy_number=policy.policy_number,
            current_premium=policy.premium,
            renewal_premium=offered,
            renewal_effective_date=policy.expiration_date,
            status=policy.status,
        )


class GetIdCard:
    """Build an insurance ID card."""

    def __init__(self, policies: PolicyRepository) -> None:
        """Store the repository.

        Args:
            policies: Policy repository.
        """
        self._policies = policies

    def execute(self, auth: AuthContext, policy_number: str) -> IdCard:
        """Return the card for one policy.

        Args:
            auth: Verified caller.
            policy_number: Policy number.

        Returns:
            ID card, including vehicles when the policy is auto or truck.
        """
        policy = require_policy(self._policies, auth, policy_number)
        vehicles = tuple(self._policies.list_vehicles(auth, policy.policy_number))
        return IdCard(
            policy_number=policy.policy_number,
            insured_name=policy.insured_name,
            line_of_business=policy.line_of_business,
            effective_date=policy.effective_date,
            expiration_date=policy.expiration_date,
            property_address=policy.property_address,
            vehicles=vehicles,
        )


class ListDocuments:
    """List document metadata."""

    def __init__(self, policies: PolicyRepository) -> None:
        """Store the repository.

        Args:
            policies: Policy repository.
        """
        self._policies = policies

    def execute(self, auth: AuthContext, policy_number: str | None) -> list[DocumentSummary]:
        """List the caller's documents, optionally for one policy.

        Args:
            auth: Verified caller.
            policy_number: Policy filter, or None for every policy.

        Returns:
            Document summaries without file bodies.
        """
        number: str | None = None
        if policy_number is not None:
            number = require_policy(self._policies, auth, policy_number).policy_number
        return self._policies.list_documents(auth, number)


class DownloadDocument:
    """Download one owned document."""

    def __init__(self, policies: PolicyRepository) -> None:
        """Store the repository.

        Args:
            policies: Policy repository.
        """
        self._policies = policies

    def execute(self, auth: AuthContext, document_id: str) -> DocumentFile:
        """Return the file body.

        Args:
            auth: Verified caller.
            document_id: Document identifier.

        Returns:
            Document metadata and body.

        Raises:
            DocumentNotFound: The caller does not have this document.
        """
        document = self._policies.get_document(auth, document_id)
        if document is None:
            raise DocumentNotFound("Document was not found.")
        return document


class ListVehicles:
    """List vehicles on one policy."""

    def __init__(self, policies: PolicyRepository) -> None:
        """Store the repository.

        Args:
            policies: Policy repository.
        """
        self._policies = policies

    def execute(self, auth: AuthContext, policy_number: str) -> list[Vehicle]:
        """Return vehicles for an owned policy.

        Args:
            auth: Verified caller.
            policy_number: Policy number.

        Returns:
            Vehicles. Home policies return an empty list.
        """
        policy = require_policy(self._policies, auth, policy_number)
        return self._policies.list_vehicles(auth, policy.policy_number)


class AddVehicle:
    """Add a vehicle to an auto or truck policy."""

    def __init__(self, policies: PolicyRepository) -> None:
        """Store the repository.

        Args:
            policies: Policy repository.
        """
        self._policies = policies

    def execute(self, auth: AuthContext, policy_number: str, command: NewVehicle) -> Vehicle:
        """Add a vehicle.

        Args:
            auth: Verified caller.
            policy_number: Policy number.
            command: Year, make, model, and VIN.

        Returns:
            The stored vehicle.

        Raises:
            VehiclesNotAllowed: The policy is a home policy.
            InvalidVehicle: The vehicle details are incomplete.
        """
        policy = require_policy(self._policies, auth, policy_number)
        if not policy.policy_number.startswith("AUTO-"):
            raise VehiclesNotAllowed("Vehicles can only be changed on auto or truck policies.")
        make = command.make.strip()
        model_name = command.model.strip()
        vin = command.vin.strip().upper()
        year_ok = 1980 <= command.year <= 2035
        details_ok = bool(make and model_name and len(vin) >= 6)
        if not year_ok or not details_ok:
            raise InvalidVehicle(
                "Enter a year from 1980 to 2035, a make, a model, "
                "and a VIN of at least 6 characters."
            )
        vehicle = Vehicle(
            vehicle_id=str(uuid4()),
            policy_number=policy.policy_number,
            year=command.year,
            make=make,
            model=model_name,
            vin=vin,
        )
        if not self._policies.add_vehicle(auth, vehicle):
            raise PolicyNotFound("Policy was not found.")
        return vehicle


class RemoveVehicle:
    """Remove a vehicle from an auto or truck policy."""

    def __init__(self, policies: PolicyRepository) -> None:
        """Store the repository.

        Args:
            policies: Policy repository.
        """
        self._policies = policies

    def execute(self, auth: AuthContext, policy_number: str, vehicle_id: str) -> None:
        """Remove a vehicle.

        Args:
            auth: Verified caller.
            policy_number: Policy number.
            vehicle_id: Vehicle identifier.

        Raises:
            VehiclesNotAllowed: The policy is a home policy.
            VehicleNotFound: The vehicle is not on this policy.
        """
        policy = require_policy(self._policies, auth, policy_number)
        if not policy.policy_number.startswith("AUTO-"):
            raise VehiclesNotAllowed("Vehicles can only be changed on auto or truck policies.")
        if not self._policies.remove_vehicle(auth, policy.policy_number, vehicle_id):
            raise VehicleNotFound("Vehicle was not found.")


class ListDrivers:
    """List drivers on one policy."""

    def __init__(self, policies: PolicyRepository) -> None:
        """Store the repository.

        Args:
            policies: Policy repository.
        """
        self._policies = policies

    def execute(self, auth: AuthContext, policy_number: str) -> list[Driver]:
        """Return drivers for an owned policy.

        Args:
            auth: Verified caller.
            policy_number: Policy number.

        Returns:
            Drivers. Home policies return an empty list.
        """
        policy = require_policy(self._policies, auth, policy_number)
        return self._policies.list_drivers(auth, policy.policy_number)


class AddDriver:
    """Add a driver to an auto or truck policy."""

    def __init__(self, policies: PolicyRepository) -> None:
        """Store the repository.

        Args:
            policies: Policy repository.
        """
        self._policies = policies

    def execute(self, auth: AuthContext, policy_number: str, command: NewDriver) -> Driver:
        """Add a driver.

        Args:
            auth: Verified caller.
            policy_number: Policy number.
            command: Name, license number, and date of birth.

        Returns:
            The stored driver.

        Raises:
            DriversNotAllowed: The policy is a home policy.
            InvalidDriver: The driver details are incomplete.
        """
        policy = require_policy(self._policies, auth, policy_number)
        if not policy.policy_number.startswith("AUTO-"):
            raise DriversNotAllowed("Drivers can only be changed on auto or truck policies.")
        full_name = command.full_name.strip()
        license_number = command.license_number.strip().upper()
        if len(full_name) < 2 or len(license_number) < 4:
            raise InvalidDriver("Enter the driver name and a license number.")
        if command.date_of_birth >= date.today():
            raise InvalidDriver("Date of birth must be in the past.")
        driver = Driver(
            driver_id=str(uuid4()),
            policy_number=policy.policy_number,
            full_name=full_name,
            license_number=license_number,
            date_of_birth=command.date_of_birth,
        )
        if not self._policies.add_driver(auth, driver):
            raise PolicyNotFound("Policy was not found.")
        return driver


class RemoveDriver:
    """Remove a driver from an auto or truck policy."""

    def __init__(self, policies: PolicyRepository) -> None:
        """Store the repository.

        Args:
            policies: Policy repository.
        """
        self._policies = policies

    def execute(self, auth: AuthContext, policy_number: str, driver_id: str) -> None:
        """Remove a driver.

        Args:
            auth: Verified caller.
            policy_number: Policy number.
            driver_id: Driver identifier.

        Raises:
            DriversNotAllowed: The policy is a home policy.
            DriverNotFound: The driver is not on this policy.
        """
        policy = require_policy(self._policies, auth, policy_number)
        if not policy.policy_number.startswith("AUTO-"):
            raise DriversNotAllowed("Drivers can only be changed on auto or truck policies.")
        if not self._policies.remove_driver(auth, policy.policy_number, driver_id):
            raise DriverNotFound("Driver was not found.")


class SubmitClaim:
    """File a claim against an owned policy."""

    def __init__(self, policies: PolicyRepository) -> None:
        """Store the repository.

        Args:
            policies: Policy repository.
        """
        self._policies = policies

    def execute(self, auth: AuthContext, policy_number: str, description: str) -> Claim:
        """Store a submitted claim.

        Args:
            auth: Verified caller.
            policy_number: Policy number.
            description: What happened.

        Returns:
            The stored claim.

        Raises:
            InvalidClaim: The description is too short or too long.
        """
        policy = require_policy(self._policies, auth, policy_number)
        text = description.strip()
        if len(text) < 10 or len(text) > 2000:
            raise InvalidClaim("Describe the claim in 10 to 2000 characters.")
        claim = Claim(
            claim_id=str(uuid4()),
            policy_number=policy.policy_number,
            description=text,
            status="submitted",
            filed_at=datetime.now(UTC),
        )
        if not self._policies.add_claim(auth, claim):
            raise PolicyNotFound("Policy was not found.")
        return claim


class ListClaims:
    """List claims on one policy."""

    def __init__(self, policies: PolicyRepository) -> None:
        """Store the repository.

        Args:
            policies: Policy repository.
        """
        self._policies = policies

    def execute(self, auth: AuthContext, policy_number: str) -> list[Claim]:
        """Return claims for an owned policy.

        Args:
            auth: Verified caller.
            policy_number: Policy number.

        Returns:
            Claims filed by the caller.
        """
        policy = require_policy(self._policies, auth, policy_number)
        return self._policies.list_claims(auth, policy.policy_number)
