"""HTTP adapter for the contact service."""

from collections.abc import Callable

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from portal_common.identity import AuthContext
from pydantic import BaseModel, ConfigDict
from starlette.requests import Request

from contact_service.domain.errors import ContactError
from contact_service.domain.models import AgentCall, AgentMessage
from contact_service.domain.use_cases import ListCalls, ListMessages, SendMessage, StartCall

_STATUS: dict[str, int] = {
    "invalid_message": 400,
    "invalid_phone_number": 400,
}


class MessageBody(BaseModel):
    """JSON body for a message to the agent.

    Attributes:
        body: Message text.
    """

    model_config = ConfigDict(extra="forbid")

    body: str


class CallBody(BaseModel):
    """JSON body for a mock call.

    Attributes:
        phone_number: Number the customer wants used.
    """

    model_config = ConfigDict(extra="forbid")

    phone_number: str


def _message_json(message: AgentMessage) -> dict[str, str]:
    """Map a message to JSON.

    Args:
        message: Stored message.

    Returns:
        JSON-ready dictionary.
    """
    return {
        "message_id": message.message_id,
        "body": message.body,
        "created_at": message.created_at.isoformat(),
        "twilio_sid": message.twilio_sid,
    }


def _call_json(call: AgentCall) -> dict[str, str]:
    """Map a call to JSON.

    Args:
        call: Stored call.

    Returns:
        JSON-ready dictionary.
    """
    return {
        "call_id": call.call_id,
        "phone_number": call.phone_number,
        "created_at": call.created_at.isoformat(),
        "twilio_sid": call.twilio_sid,
    }


def create_app(
    send_message: SendMessage,
    list_messages: ListMessages,
    start_call: StartCall,
    list_calls: ListCalls,
    require_auth: Callable[..., AuthContext],
) -> FastAPI:
    """Build the contact HTTP application.

    Args:
        send_message: Message use case.
        list_messages: Message history use case.
        start_call: Call use case.
        list_calls: Call history use case.
        require_auth: FastAPI dependency that yields an AuthContext.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(title="Contact Service")

    @app.exception_handler(ContactError)
    async def handle_contact_error(_request: Request, exc: ContactError) -> JSONResponse:
        """Map a domain error to a JSON response.

        Args:
            _request: Incoming request. Unused.
            exc: Domain error raised by a use case.

        Returns:
            JSON body with an English message.
        """
        return JSONResponse(
            status_code=_STATUS.get(exc.code, 400),
            content={"error": exc.code, "message": exc.message},
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        """Report that the process is up.

        Returns:
            A static status object.
        """
        return {"status": "ok"}

    @app.get("/contact/messages")
    def messages(auth: AuthContext = Depends(require_auth)) -> dict[str, object]:
        """List messages.

        Args:
            auth: Verified caller.

        Returns:
            A messages array.
        """
        return {"messages": [_message_json(item) for item in list_messages.execute(auth)]}

    @app.post("/contact/messages", status_code=201)
    def create_message(
        body: MessageBody, auth: AuthContext = Depends(require_auth)
    ) -> dict[str, str]:
        """Send a mock SMS.

        Args:
            body: Message JSON.
            auth: Verified caller.

        Returns:
            The stored message, including a fake Twilio SID.
        """
        return _message_json(send_message.execute(auth, body.body))

    @app.get("/contact/calls")
    def calls(auth: AuthContext = Depends(require_auth)) -> dict[str, object]:
        """List calls.

        Args:
            auth: Verified caller.

        Returns:
            A calls array.
        """
        return {"calls": [_call_json(item) for item in list_calls.execute(auth)]}

    @app.post("/contact/calls", status_code=201)
    def create_call(body: CallBody, auth: AuthContext = Depends(require_auth)) -> dict[str, str]:
        """Start a mock call.

        Args:
            body: Call JSON.
            auth: Verified caller.

        Returns:
            The stored call, including a fake Twilio SID.
        """
        return _call_json(start_call.execute(auth, body.phone_number))

    return app
