"""Use-case tests for mock messages and calls."""

from portal_common.identity import AuthContext

from contact_service.domain.errors import InvalidPhoneNumber
from contact_service.domain.models import AgentCall, AgentMessage
from contact_service.domain.use_cases import ListMessages, SendMessage, StartCall


class FakeMessages:
    """In-memory messages filtered by caller."""

    def __init__(self) -> None:
        """Start empty."""
        self.rows: list[tuple[str, AgentMessage]] = []

    def add(self, auth: AuthContext, message: AgentMessage) -> None:
        """Store a message.

        Args:
            auth: Verified caller.
            message: Message to persist.
        """
        self.rows.append((auth.user_id, message))

    def list_messages(self, auth: AuthContext) -> list[AgentMessage]:
        """List the caller's messages.

        Args:
            auth: Verified caller.

        Returns:
            Owned messages.
        """
        return [message for owner, message in self.rows if owner == auth.user_id]


class FakeCalls:
    """In-memory calls filtered by caller."""

    def __init__(self) -> None:
        """Start empty."""
        self.rows: list[tuple[str, AgentCall]] = []

    def add_call(self, auth: AuthContext, call: AgentCall) -> None:
        """Store a call.

        Args:
            auth: Verified caller.
            call: Call to persist.
        """
        self.rows.append((auth.user_id, call))

    def list_calls(self, auth: AuthContext) -> list[AgentCall]:
        """List the caller's calls.

        Args:
            auth: Verified caller.

        Returns:
            Owned calls.
        """
        return [call for owner, call in self.rows if owner == auth.user_id]


class FakeTwilio:
    """Records provider attempts and returns deterministic SIDs."""

    def __init__(self) -> None:
        """Start with empty logs."""
        self.messages: list[tuple[str, str]] = []
        self.calls: list[tuple[str, str]] = []

    def send_sms(self, auth: AuthContext, body: str) -> str:
        """Record an SMS.

        Args:
            auth: Verified caller.
            body: Message text.

        Returns:
            A fake message SID.
        """
        self.messages.append((auth.user_id, body))
        return "SMtest"

    def start_call(self, auth: AuthContext, phone_number: str) -> str:
        """Record a call.

        Args:
            auth: Verified caller.
            phone_number: Dialed number.

        Returns:
            A fake call SID.
        """
        self.calls.append((auth.user_id, phone_number))
        return "CAtest"


def test_message_and_call_use_the_mock_provider_and_stay_private() -> None:
    """SIDs come from the mock, and another customer's history is hidden."""
    messages = FakeMessages()
    calls = FakeCalls()
    twilio = FakeTwilio()
    auth = AuthContext(user_id="user-1", email="a@example.com", token="token")
    other = AuthContext(user_id="user-2", email="b@example.com", token="other")
    sent = SendMessage(messages, twilio).execute(auth, "Please call me about AUTO-1001.")
    assert sent.twilio_sid == "SMtest"
    assert twilio.messages == [("user-1", "Please call me about AUTO-1001.")]
    SendMessage(messages, twilio).execute(other, "This belongs to someone else.")
    visible = ListMessages(messages).execute(auth)
    assert [item.body for item in visible] == ["Please call me about AUTO-1001."]
    started = StartCall(calls, twilio).execute(auth, "+1 512 555 0142")
    assert started.twilio_sid == "CAtest"
    try:
        StartCall(calls, twilio).execute(auth, "not-a-phone")
    except InvalidPhoneNumber:
        pass
    else:
        raise AssertionError("an invalid phone number was accepted")
