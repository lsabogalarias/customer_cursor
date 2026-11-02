"""In-memory policy store for use-case tests."""

from portal_common.identity import AuthContext

from policy_service.domain.models import (
    Claim,
    DocumentFile,
    DocumentSummary,
    Driver,
    Policy,
    PolicyStatus,
    Vehicle,
)


class FakePolicyRepository:
    """Filters every read and write by the caller id."""

    def __init__(self) -> None:
        """Start with empty collections."""
        self.policies: list[Policy] = []
        self.vehicles: list[Vehicle] = []
        self.vehicle_owners: dict[str, str] = {}
        self.drivers: list[Driver] = []
        self.driver_owners: dict[str, str] = {}
        self.documents: list[DocumentFile] = []
        self.document_owners: dict[str, str] = {}
        self.claims: list[Claim] = []
        self.claim_owners: dict[str, str] = {}

    def list_policies(self, auth: AuthContext) -> list[Policy]:
        """List the caller's policies.

        Args:
            auth: Verified caller.

        Returns:
            Owned policies.
        """
        return [item for item in self.policies if item.user_id == auth.user_id]

    def get_policy(self, auth: AuthContext, policy_number: str) -> Policy | None:
        """Load one owned policy.

        Args:
            auth: Verified caller.
            policy_number: Policy number.

        Returns:
            The policy, or None.
        """
        for item in self.policies:
            if item.user_id == auth.user_id and item.policy_number == policy_number:
                return item
        return None

    def save_status(
        self, auth: AuthContext, policy_number: str, status: PolicyStatus
    ) -> Policy | None:
        """Update status for an owned policy.

        Args:
            auth: Verified caller.
            policy_number: Policy number.
            status: New status.

        Returns:
            The updated policy, or None.
        """
        for index, item in enumerate(self.policies):
            if item.user_id == auth.user_id and item.policy_number == policy_number:
                updated = item.model_copy(update={"status": status})
                self.policies[index] = updated
                return updated
        return None

    def list_vehicles(self, auth: AuthContext, policy_number: str) -> list[Vehicle]:
        """List owned vehicles.

        Args:
            auth: Verified caller.
            policy_number: Policy number.

        Returns:
            Vehicles.
        """
        return [
            item
            for item in self.vehicles
            if item.policy_number == policy_number
            and self.vehicle_owners.get(item.vehicle_id) == auth.user_id
        ]

    def add_vehicle(self, auth: AuthContext, vehicle: Vehicle) -> bool:
        """Insert a vehicle when the policy is owned.

        Args:
            auth: Verified caller.
            vehicle: Vehicle to insert.

        Returns:
            True when the policy belongs to the caller.
        """
        if self.get_policy(auth, vehicle.policy_number) is None:
            return False
        self.vehicles.append(vehicle)
        self.vehicle_owners[vehicle.vehicle_id] = auth.user_id
        return True

    def remove_vehicle(self, auth: AuthContext, policy_number: str, vehicle_id: str) -> bool:
        """Delete an owned vehicle.

        Args:
            auth: Verified caller.
            policy_number: Policy number.
            vehicle_id: Vehicle identifier.

        Returns:
            True when a row was removed.
        """
        for item in list(self.vehicles):
            if (
                item.vehicle_id == vehicle_id
                and item.policy_number == policy_number
                and self.vehicle_owners.get(vehicle_id) == auth.user_id
            ):
                self.vehicles.remove(item)
                return True
        return False

    def list_drivers(self, auth: AuthContext, policy_number: str) -> list[Driver]:
        """List owned drivers.

        Args:
            auth: Verified caller.
            policy_number: Policy number.

        Returns:
            Drivers.
        """
        return [
            item
            for item in self.drivers
            if item.policy_number == policy_number
            and self.driver_owners.get(item.driver_id) == auth.user_id
        ]

    def add_driver(self, auth: AuthContext, driver: Driver) -> bool:
        """Insert a driver when the policy is owned.

        Args:
            auth: Verified caller.
            driver: Driver to insert.

        Returns:
            True when the policy belongs to the caller.
        """
        if self.get_policy(auth, driver.policy_number) is None:
            return False
        self.drivers.append(driver)
        self.driver_owners[driver.driver_id] = auth.user_id
        return True

    def remove_driver(self, auth: AuthContext, policy_number: str, driver_id: str) -> bool:
        """Delete an owned driver.

        Args:
            auth: Verified caller.
            policy_number: Policy number.
            driver_id: Driver identifier.

        Returns:
            True when a row was removed.
        """
        return False

    def list_documents(
        self, auth: AuthContext, policy_number: str | None
    ) -> list[DocumentSummary]:
        """List owned document metadata.

        Args:
            auth: Verified caller.
            policy_number: Optional filter.

        Returns:
            Summaries.
        """
        found: list[DocumentSummary] = []
        for item in self.documents:
            if self.document_owners.get(item.document_id) != auth.user_id:
                continue
            if policy_number is not None and item.policy_number != policy_number:
                continue
            found.append(
                DocumentSummary(
                    document_id=item.document_id,
                    policy_number=item.policy_number,
                    title=item.title,
                    file_name=item.file_name,
                    content_type=item.content_type,
                )
            )
        return found

    def get_document(self, auth: AuthContext, document_id: str) -> DocumentFile | None:
        """Load an owned document.

        Args:
            auth: Verified caller.
            document_id: Document identifier.

        Returns:
            The file, or None.
        """
        for item in self.documents:
            owned = self.document_owners.get(document_id) == auth.user_id
            if item.document_id == document_id and owned:
                return item
        return None

    def add_claim(self, auth: AuthContext, claim: Claim) -> bool:
        """Insert a claim when the policy is owned.

        Args:
            auth: Verified caller.
            claim: Claim to insert.

        Returns:
            True when the policy belongs to the caller.
        """
        if self.get_policy(auth, claim.policy_number) is None:
            return False
        self.claims.append(claim)
        self.claim_owners[claim.claim_id] = auth.user_id
        return True

    def list_claims(self, auth: AuthContext, policy_number: str) -> list[Claim]:
        """List owned claims.

        Args:
            auth: Verified caller.
            policy_number: Policy number.

        Returns:
            Claims.
        """
        return [
            item
            for item in self.claims
            if item.policy_number == policy_number
            and self.claim_owners.get(item.claim_id) == auth.user_id
        ]
