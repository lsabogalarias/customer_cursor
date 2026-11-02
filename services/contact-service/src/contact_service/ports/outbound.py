"""Outbound ports for contact history and the mock Twilio provider."""

from typing import Protocol

from portal_common.identity import AuthContext

from contact_service.domain.models import AgentCall, AgentMessage


class MessageRepository(Protocol):
    """Customer-scoped message history."""

    def add(self, auth: AuthContext, message: AgentMessage) -> None:
        """Store a message for the caller.

        Args:
            auth: Verified caller.
            message: Message to persist.
        """
        ...

    def list_messages(self, auth: AuthContext) -> list[AgentMessage]:
        """List the caller's messages.

        Args:
            auth: Verified caller.

        Returns:
            Messages, newest last.
        """
        ...


class CallRepository(Protocol):
    """Customer-scoped call history."""

    def add_call(self, auth: AuthContext, call: AgentCall) -> None:
        """Store a call for the caller.

        Args:
            auth: Verified caller.
            call: Call to persist.
        """
        ...

    def list_calls(self, auth: AuthContext) -> list[AgentCall]:
        """List the caller's calls.

        Args:
            auth: Verified caller.

        Returns:
            Calls, newest last.
        """
        ...


class TwilioProvider(Protocol):
    """Mock SMS and voice provider. Implementations must not open a network connection."""

    def send_sms(self, auth: AuthContext, body: str) -> str:
        """Record an SMS and return a fake SID.

        Args:
            auth: Verified caller.
            body: Message text.

        Returns:
            A fake Twilio message SID.
        """
        ...

    def start_call(self, auth: AuthContext, phone_number: str) -> str:
        """Record a voice call and return a fake SID.

        Args:
            auth: Verified caller.
            phone_number: Number that would be dialed.

        Returns:
            A fake Twilio call SID.
        """
        ...
