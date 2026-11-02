"""Inbound port for sending a message."""

from typing import Protocol

from portal_common.identity import AuthContext

from contact_service.domain.models import AgentMessage


class SendMessagePort(Protocol):
    """Ask the service to record a message to the agent."""

    def execute(self, auth: AuthContext, body: str) -> AgentMessage:
        """Store a message and a fake Twilio SID.

        Args:
            auth: Verified caller.
            body: Message text.

        Returns:
            The stored message.
        """
        ...
