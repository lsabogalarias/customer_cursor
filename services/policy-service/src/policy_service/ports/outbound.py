"""Outbound ports for policy data."""

from typing import Protocol

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


class PolicyRepository(Protocol):
    """Customer-scoped policy storage.

    Every method takes AuthContext and applies the ownership filter in the
    query. A missing row and a row owned by someone else both come back empty.
    """

    def list_policies(self, auth: AuthContext) -> list[Policy]:
        """List the caller's policies.

        Args:
            auth: Verified caller.

        Returns:
            Policies owned by the caller, ordered by policy number.
        """
        ...

    def get_policy(self, auth: AuthContext, policy_number: str) -> Policy | None:
        """Load one policy when the caller owns it.

        Args:
            auth: Verified caller.
            policy_number: Normalized policy number.

        Returns:
            The policy, or None.
        """
        ...

    def save_status(
        self, auth: AuthContext, policy_number: str, status: PolicyStatus
    ) -> Policy | None:
        """Update status when the caller owns the policy.

        Args:
            auth: Verified caller.
            policy_number: Normalized policy number.
            status: New status.

        Returns:
            The updated policy, or None when it is not owned.
        """
        ...

    def list_vehicles(self, auth: AuthContext, policy_number: str) -> list[Vehicle]:
        """List vehicles on a policy the caller owns.

        Args:
            auth: Verified caller.
            policy_number: Normalized policy number.

        Returns:
            Vehicles, or an empty list when none exist.
        """
        ...

    def add_vehicle(self, auth: AuthContext, vehicle: Vehicle) -> bool:
        """Insert a vehicle when the caller owns the policy.

        Args:
            auth: Verified caller.
            vehicle: Vehicle to insert.

        Returns:
            True when a row was inserted.
        """
        ...

    def remove_vehicle(self, auth: AuthContext, policy_number: str, vehicle_id: str) -> bool:
        """Delete a vehicle when the caller owns it.

        Args:
            auth: Verified caller.
            policy_number: Normalized policy number.
            vehicle_id: Vehicle identifier.

        Returns:
            True when a row was deleted.
        """
        ...

    def list_drivers(self, auth: AuthContext, policy_number: str) -> list[Driver]:
        """List drivers on a policy the caller owns.

        Args:
            auth: Verified caller.
            policy_number: Normalized policy number.

        Returns:
            Drivers, or an empty list.
        """
        ...

    def add_driver(self, auth: AuthContext, driver: Driver) -> bool:
        """Insert a driver when the caller owns the policy.

        Args:
            auth: Verified caller.
            driver: Driver to insert.

        Returns:
            True when a row was inserted.
        """
        ...

    def remove_driver(self, auth: AuthContext, policy_number: str, driver_id: str) -> bool:
        """Delete a driver when the caller owns it.

        Args:
            auth: Verified caller.
            policy_number: Normalized policy number.
            driver_id: Driver identifier.

        Returns:
            True when a row was deleted.
        """
        ...

    def list_documents(
        self, auth: AuthContext, policy_number: str | None
    ) -> list[DocumentSummary]:
        """List document metadata for the caller.

        Args:
            auth: Verified caller.
            policy_number: Optional policy filter.

        Returns:
            Document summaries.
        """
        ...

    def get_document(self, auth: AuthContext, document_id: str) -> DocumentFile | None:
        """Load a document body when the caller owns it.

        Args:
            auth: Verified caller.
            document_id: Document identifier.

        Returns:
            The file, or None.
        """
        ...

    def add_claim(self, auth: AuthContext, claim: Claim) -> bool:
        """Insert a claim when the caller owns the policy.

        Args:
            auth: Verified caller.
            claim: Claim to insert.

        Returns:
            True when a row was inserted.
        """
        ...

    def list_claims(self, auth: AuthContext, policy_number: str) -> list[Claim]:
        """List claims on a policy the caller owns.

        Args:
            auth: Verified caller.
            policy_number: Normalized policy number.

        Returns:
            Claims, newest last.
        """
        ...
