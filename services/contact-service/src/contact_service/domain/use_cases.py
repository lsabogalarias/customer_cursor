"""Use cases for mock messages and calls."""

import re
from datetime import UTC, datetime
from uuid import uuid4

from portal_common.identity import AuthContext

from contact_service.domain.errors import InvalidMessage, InvalidPhoneNumber
from contact_service.domain.models import AgentCall, AgentMessage
from contact_service.ports.outbound import CallRepository, MessageRepository, TwilioProvider

_PHONE = re.compile(r"^\+?[0-9][0-9\-\s()]{6,20}$")


class SendMessage:
    """Send a message to the agent through the mock provider."""

    def __init__(self, messages: MessageRepository, twilio: TwilioProvider) -> None:
        """Store the ports.

        Args:
            messages: Message repository.
            twilio: Mock Twilio provider.
        """
        self._messages = messages
        self._twilio = twilio

    def execute(self, auth: AuthContext, body: str) -> AgentMessage:
        """Store a message and a fake Twilio SID.

        Args:
            auth: Verified caller.
            body: Message text.

        Returns:
            The stored message.

        Raises:
            InvalidMessage: The body is empty or longer than 2000 characters.
        """
        text = body.strip()
        if not text or len(text) > 2000:
            raise InvalidMessage("Enter a message of 1 to 2000 characters.")
        message = AgentMessage(
            message_id=str(uuid4()),
            body=text,
            created_at=datetime.now(UTC),
            twilio_sid=self._twilio.send_sms(auth, text),
        )
        self._messages.add(auth, message)
        return message


class ListMessages:
    """List messages the caller has sent."""

    def __init__(self, messages: MessageRepository) -> None:
        """Store the repository.

        Args:
            messages: Message repository.
        """
        self._messages = messages

    def execute(self, auth: AuthContext) -> list[AgentMessage]:
        """Return the caller's messages.

        Args:
            auth: Verified caller.

        Returns:
            Stored messages.
        """
        return self._messages.list_messages(auth)


class StartCall:
    """Start a mock call to the agent."""

    def __init__(self, calls: CallRepository, twilio: TwilioProvider) -> None:
        """Store the ports.

        Args:
            calls: Call repository.
            twilio: Mock Twilio provider.
        """
        self._calls = calls
        self._twilio = twilio

    def execute(self, auth: AuthContext, phone_number: str) -> AgentCall:
        """Store a call request and a fake Twilio SID.

        Args:
            auth: Verified caller.
            phone_number: Number the customer wants used for the call.

        Returns:
            The stored call.

        Raises:
            InvalidPhoneNumber: The number is not a plausible phone number.
        """
        number = phone_number.strip()
        if _PHONE.fullmatch(number) is None:
            raise InvalidPhoneNumber("Enter a phone number, for example +1 512 555 0142.")
        call = AgentCall(
            call_id=str(uuid4()),
            phone_number=number,
            created_at=datetime.now(UTC),
            twilio_sid=self._twilio.start_call(auth, number),
        )
        self._calls.add_call(auth, call)
        return call


class ListCalls:
    """List mock calls the caller has requested."""

    def __init__(self, calls: CallRepository) -> None:
        """Store the repository.

        Args:
            calls: Call repository.
        """
        self._calls = calls

    def execute(self, auth: AuthContext) -> list[AgentCall]:
        """Return the caller's calls.

        Args:
            auth: Verified caller.

        Returns:
            Stored calls.
        """
        return self._calls.list_calls(auth)
