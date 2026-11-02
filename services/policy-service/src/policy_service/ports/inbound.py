"""Inbound ports for the policy service."""

from typing import Protocol

from portal_common.identity import AuthContext

from policy_service.domain.models import Policy


class ListPoliciesPort(Protocol):
    """Ask for the caller's policies."""

    def execute(self, auth: AuthContext) -> list[Policy]:
        """Return every policy owned by the caller.

        Args:
            auth: Verified caller.

        Returns:
            The caller's policies.
        """
        ...
