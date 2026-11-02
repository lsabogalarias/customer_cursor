"""Use-case tests for policy rules."""

from datetime import date
from decimal import Decimal

from portal_common.identity import AuthContext

from policy_service.domain.errors import (
    DocumentNotFound,
    InvalidPolicyNumber,
    PolicyNotFound,
    VehiclesNotAllowed,
)
from policy_service.domain.models import (
    DocumentFile,
    LineOfBusiness,
    NewVehicle,
    Policy,
    PolicyStatus,
)
from policy_service.domain.use_cases import (
    AddVehicle,
    DownloadDocument,
    GetRenewalDetails,
    ListPolicies,
    RenewPolicy,
    SubmitClaim,
)
from tests.fakes import FakePolicyRepository


def _policy(number: str, user_id: str, premium: str = "1280.00") -> Policy:
    """Build a policy fixture.

    Args:
        number: Policy number.
        user_id: Owner id.
        premium: Term premium.

    Returns:
        A frozen policy.
    """
    line = LineOfBusiness.HOMEOWNERS if number.startswith("HOME-") else LineOfBusiness.PERSONAL_AUTO
    product = "Homeowners" if number.startswith("HOME-") else "Personal Auto"
    return Policy(
        policy_number=number,
        user_id=user_id,
        line_of_business=line,
        product_name=product,
        status=PolicyStatus.ACTIVE,
        insured_name="Alex Morgan",
        property_address="18 Cedar Lane" if number.startswith("HOME-") else None,
        effective_date=date(2026, 1, 1),
        expiration_date=date(2027, 1, 1),
        premium=Decimal(premium),
    )


def test_customers_only_see_their_own_policies() -> None:
    """A second customer's policy is invisible to the caller."""
    store = FakePolicyRepository()
    store.policies.extend(
        [_policy("AUTO-1001", "user-1"), _policy("HOME-3008", "user-2", "980.00")]
    )
    auth = AuthContext(user_id="user-1", email="a@example.com", token="token")
    found = ListPolicies(store).execute(auth)
    assert [item.policy_number for item in found] == ["AUTO-1001"]
    try:
        RenewPolicy(store).execute(auth, "HOME-3008")
    except PolicyNotFound:
        pass
    else:
        raise AssertionError("another customer's policy was visible")


def test_home_policies_reject_vehicles_and_auto_policies_accept_them() -> None:
    """Vehicle changes follow the policy prefix."""
    store = FakePolicyRepository()
    store.policies.extend([_policy("AUTO-1001", "user-1"), _policy("HOME-3008", "user-1")])
    auth = AuthContext(user_id="user-1", email="a@example.com", token="token")
    use_case = AddVehicle(store)
    try:
        use_case.execute(
            auth,
            "HOME-3008",
            NewVehicle(year=2022, make="Toyota", model="Camry", vin="ABC123456"),
        )
    except VehiclesNotAllowed:
        pass
    else:
        raise AssertionError("a home policy accepted a vehicle")
    vehicle = use_case.execute(
        auth,
        "auto-1001",
        NewVehicle(year=2022, make="Toyota", model="Camry", vin="abc123456"),
    )
    assert vehicle.policy_number == "AUTO-1001"
    assert vehicle.vin == "ABC123456"


def test_renewal_quote_is_five_percent_and_renew_is_idempotent() -> None:
    """The offered premium is rounded half up, and renew can be repeated."""
    store = FakePolicyRepository()
    store.policies.append(_policy("AUTO-1001", "user-1", "1280.00"))
    store.policies.append(_policy("AUTO-2044", "user-1", "10.01"))
    auth = AuthContext(user_id="user-1", email="a@example.com", token="token")
    first = GetRenewalDetails(store).execute(auth, "AUTO-1001")
    second = GetRenewalDetails(store).execute(auth, "AUTO-2044")
    assert first.renewal_premium == Decimal("1344.00")
    assert second.renewal_premium == Decimal("10.51")
    renewed = RenewPolicy(store).execute(auth, "AUTO-1001")
    assert renewed.status is PolicyStatus.RENEWAL_REQUESTED
    again = RenewPolicy(store).execute(auth, "AUTO-1001")
    assert again.status is PolicyStatus.RENEWAL_REQUESTED


def test_invalid_numbers_are_rejected_and_claims_stay_on_the_policy() -> None:
    """Malformed numbers fail before a lookup. A claim is stored for the owner."""
    store = FakePolicyRepository()
    store.policies.append(_policy("AUTO-1001", "user-1"))
    auth = AuthContext(user_id="user-1", email="a@example.com", token="token")
    try:
        SubmitClaim(store).execute(auth, "AUTO-1", "A long enough claim description.")
    except InvalidPolicyNumber:
        pass
    else:
        raise AssertionError("a short policy number was accepted")
    claim = SubmitClaim(store).execute(
        auth, "AUTO-1001", "Rear bumper was damaged in a parking lot."
    )
    assert claim.status == "submitted"
    assert claim.policy_number == "AUTO-1001"


def test_document_download_does_not_cross_customers() -> None:
    """Another customer's file is not found."""
    store = FakePolicyRepository()
    store.documents.append(
        DocumentFile(
            document_id="doc-1",
            policy_number="AUTO-1001",
            title="Declarations Page",
            file_name="declarations.txt",
            content_type="text/plain",
            body="Private declarations",
        )
    )
    store.document_owners["doc-1"] = "user-2"
    auth = AuthContext(user_id="user-1", email="a@example.com", token="token")
    try:
        DownloadDocument(store).execute(auth, "doc-1")
    except DocumentNotFound:
        pass
    else:
        raise AssertionError("another customer's document was returned")
