"""Policy domain models."""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class LineOfBusiness(StrEnum):
    """Product family stored on a policy."""

    PERSONAL_AUTO = "personal_auto"
    TRUCK = "truck"
    HOMEOWNERS = "homeowners"


class PolicyStatus(StrEnum):
    """Lifecycle state the portal is allowed to show."""

    ACTIVE = "active"
    RENEWAL_REQUESTED = "renewal_requested"


class Policy(BaseModel):
    """A customer's auto, truck, or home policy.

    Attributes:
        policy_number: ``AUTO-XXXX`` or ``HOME-XXXX``.
        user_id: Owner. Omitted from API responses.
        line_of_business: Product family.
        product_name: English product label.
        status: Active or renewal requested.
        insured_name: Name printed on documents.
        property_address: Home address, or None for vehicle policies.
        effective_date: Date cover starts.
        expiration_date: Date cover ends.
        premium: Term premium in dollars.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    policy_number: str
    user_id: str
    line_of_business: LineOfBusiness
    product_name: str
    status: PolicyStatus
    insured_name: str
    property_address: str | None
    effective_date: date
    expiration_date: date
    premium: Decimal


class Vehicle(BaseModel):
    """A vehicle listed on an auto or truck policy.

    Attributes:
        vehicle_id: Stable identifier.
        policy_number: Owning policy.
        year: Model year.
        make: Manufacturer.
        model: Model name.
        vin: Vehicle identification number.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    vehicle_id: str
    policy_number: str
    year: int
    make: str
    model: str
    vin: str


class Driver(BaseModel):
    """A driver listed on an auto or truck policy.

    Attributes:
        driver_id: Stable identifier.
        policy_number: Owning policy.
        full_name: Driver name.
        license_number: Driver license number.
        date_of_birth: Date of birth.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    driver_id: str
    policy_number: str
    full_name: str
    license_number: str
    date_of_birth: date


class NewVehicle(BaseModel):
    """Fields the customer supplies when adding a vehicle.

    Attributes:
        year: Model year.
        make: Manufacturer.
        model: Model name.
        vin: Vehicle identification number.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    year: int
    make: str
    model: str
    vin: str


class NewDriver(BaseModel):
    """Fields the customer supplies when adding a driver.

    Attributes:
        full_name: Driver name.
        license_number: Driver license number.
        date_of_birth: Date of birth.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    full_name: str
    license_number: str
    date_of_birth: date


class DocumentSummary(BaseModel):
    """Document metadata without the file body.

    Attributes:
        document_id: Stable identifier.
        policy_number: Owning policy.
        title: English title.
        file_name: Download file name.
        content_type: MIME type.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    document_id: str
    policy_number: str
    title: str
    file_name: str
    content_type: str


class DocumentFile(DocumentSummary):
    """Document metadata plus the file body.

    Attributes:
        body: UTF-8 text stored for the mock document.
    """

    body: str


class Claim(BaseModel):
    """A claim submitted by the customer.

    Attributes:
        claim_id: Stable identifier.
        policy_number: Policy the claim is filed against.
        description: Customer description.
        status: Always ``submitted`` for this POC.
        filed_at: UTC timestamp.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    claim_id: str
    policy_number: str
    description: str
    status: str
    filed_at: datetime


class RenewalQuote(BaseModel):
    """Renewal figures derived from the current term.

    Attributes:
        policy_number: Policy being renewed.
        current_premium: Premium of the current term.
        renewal_premium: Offered premium.
        renewal_effective_date: Date the renewal would start.
        status: Current policy status.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    policy_number: str
    current_premium: Decimal
    renewal_premium: Decimal
    renewal_effective_date: date
    status: PolicyStatus


class IdCard(BaseModel):
    """Proof-of-insurance card for one policy.

    Attributes:
        policy_number: Policy printed on the card.
        insured_name: Named insured.
        line_of_business: Product family.
        effective_date: Date cover starts.
        expiration_date: Date cover ends.
        property_address: Home address, or None for vehicle policies.
        vehicles: Vehicles printed on an auto or truck card.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    policy_number: str
    insured_name: str
    line_of_business: LineOfBusiness
    effective_date: date
    expiration_date: date
    property_address: str | None
    vehicles: tuple[Vehicle, ...]
