"""Contact domain models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AgentMessage(BaseModel):
    """A message stored after the mock SMS provider accepts it.

    Attributes:
        message_id: Stable identifier.
        body: Message text.
        created_at: UTC timestamp.
        twilio_sid: Fake Twilio message SID.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    message_id: str
    body: str
    created_at: datetime
    twilio_sid: str


class AgentCall(BaseModel):
    """A call stored after the mock voice provider accepts it.

    Attributes:
        call_id: Stable identifier.
        phone_number: Number the mock call would dial.
        created_at: UTC timestamp.
        twilio_sid: Fake Twilio call SID.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    call_id: str
    phone_number: str
    created_at: datetime
    twilio_sid: str
