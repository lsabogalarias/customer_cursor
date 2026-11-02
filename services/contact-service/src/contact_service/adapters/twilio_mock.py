"""In-memory Twilio stand-in. It never opens a socket."""

from uuid import uuid4

from portal_common.identity import AuthContext


class InMemoryTwilio:
    """Records SMS and call attempts inside the process."""

    def __init__(self) -> None:
        """Start with empty attempt logs."""
        self.messages: list[tuple[str, str]] = []
        self.calls: list[tuple[str, str]] = []

    def send_sms(self, auth: AuthContext, body: str) -> str:
        """Record an SMS and return a fake SID.

        Args:
            auth: Verified caller.
            body: Message text.

        Returns:
            A fake Twilio message SID.
        """
        self.messages.append((auth.user_id, body))
        return f"SM{uuid4().hex}"

    def start_call(self, auth: AuthContext, phone_number: str) -> str:
        """Record a voice call and return a fake SID.

        Args:
            auth: Verified caller.
            phone_number: Number that would be dialed.

        Returns:
            A fake Twilio call SID.
        """
        self.calls.append((auth.user_id, phone_number))
        return f"CA{uuid4().hex}"
