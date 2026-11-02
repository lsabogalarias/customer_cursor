"""Contact domain errors."""


class ContactError(Exception):
    """Base class for contact use-case failures."""

    code: str = "contact_error"

    def __init__(self, message: str) -> None:
        """Store an English explanation.

        Args:
            message: Text the HTTP adapter returns to the client.
        """
        super().__init__(message)
        self.message = message


class InvalidMessage(ContactError):
    """The message body is empty or too long."""

    code = "invalid_message"


class InvalidPhoneNumber(ContactError):
    """The phone number cannot be used for a mock call."""

    code = "invalid_phone_number"
