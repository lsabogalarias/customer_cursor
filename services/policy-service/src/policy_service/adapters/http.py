"""HTTP adapter for the policy service."""

from collections.abc import Callable
from datetime import date

from fastapi import Depends, FastAPI, Response
from fastapi.responses import JSONResponse
from portal_common.identity import AuthContext
from pydantic import BaseModel, ConfigDict
from starlette.requests import Request

from policy_service.adapters.present import (
    claim_json,
    document_json,
    driver_json,
    id_card_json,
    policy_json,
    renewal_json,
    vehicle_json,
)
from policy_service.domain.errors import InvalidDriver, PolicyError
from policy_service.domain.models import NewDriver, NewVehicle
from policy_service.domain.use_cases import (
    AddDriver,
    AddVehicle,
    DownloadDocument,
    GetIdCard,
    GetPolicy,
    GetRenewalDetails,
    ListClaims,
    ListDocuments,
    ListDrivers,
    ListPolicies,
    ListVehicles,
    RemoveDriver,
    RemoveVehicle,
    RenewPolicy,
    SubmitClaim,
)

_STATUS: dict[str, int] = {
    "invalid_policy_number": 400,
    "policy_not_found": 404,
    "vehicles_not_allowed": 400,
    "drivers_not_allowed": 400,
    "invalid_vehicle": 400,
    "invalid_driver": 400,
    "invalid_claim": 400,
    "vehicle_not_found": 404,
    "driver_not_found": 404,
    "document_not_found": 404,
}


class VehicleBody(BaseModel):
    """JSON body for a new vehicle.

    Attributes:
        year: Model year.
        make: Manufacturer.
        model: Model name.
        vin: Vehicle identification number.
    """

    model_config = ConfigDict(extra="forbid")

    year: int
    make: str
    model: str
    vin: str


class DriverBody(BaseModel):
    """JSON body for a new driver.

    Attributes:
        full_name: Driver name.
        license_number: Driver license number.
        date_of_birth: ISO date of birth.
    """

    model_config = ConfigDict(extra="forbid")

    full_name: str
    license_number: str
    date_of_birth: str


class ClaimBody(BaseModel):
    """JSON body for a new claim.

    Attributes:
        description: What happened.
    """

    model_config = ConfigDict(extra="forbid")

    description: str


def create_app(
    list_policies: ListPolicies,
    get_policy: GetPolicy,
    renew_policy: RenewPolicy,
    renewal_details: GetRenewalDetails,
    id_card: GetIdCard,
    list_documents: ListDocuments,
    download_document: DownloadDocument,
    list_vehicles: ListVehicles,
    add_vehicle: AddVehicle,
    remove_vehicle: RemoveVehicle,
    list_drivers: ListDrivers,
    add_driver: AddDriver,
    remove_driver: RemoveDriver,
    submit_claim: SubmitClaim,
    list_claims: ListClaims,
    require_auth: Callable[..., AuthContext],
) -> FastAPI:
    """Build the policy HTTP application.

    Args:
        list_policies: List use case.
        get_policy: Get use case.
        renew_policy: Renew use case.
        renewal_details: Renewal quote use case.
        id_card: ID card use case.
        list_documents: Document list use case.
        download_document: Download use case.
        list_vehicles: Vehicle list use case.
        add_vehicle: Add vehicle use case.
        remove_vehicle: Remove vehicle use case.
        list_drivers: Driver list use case.
        add_driver: Add driver use case.
        remove_driver: Remove driver use case.
        submit_claim: Claim use case.
        list_claims: Claim list use case.
        require_auth: FastAPI dependency that yields an AuthContext.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(title="Policy Service")

    @app.exception_handler(PolicyError)
    async def handle_policy_error(_request: Request, exc: PolicyError) -> JSONResponse:
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

    @app.get("/policies")
    def policies(auth: AuthContext = Depends(require_auth)) -> dict[str, object]:
        """List the caller's policies.

        Args:
            auth: Verified caller.

        Returns:
            A policies array.
        """
        return {"policies": [policy_json(item) for item in list_policies.execute(auth)]}

    @app.get("/policies/{policy_number}")
    def policy(policy_number: str, auth: AuthContext = Depends(require_auth)) -> dict[str, object]:
        """Return one policy.

        Args:
            policy_number: Policy number.
            auth: Verified caller.

        Returns:
            The policy JSON.
        """
        return policy_json(get_policy.execute(auth, policy_number))

    @app.post("/policies/{policy_number}/renew")
    def renew(policy_number: str, auth: AuthContext = Depends(require_auth)) -> dict[str, object]:
        """Request renewal.

        Args:
            policy_number: Policy number.
            auth: Verified caller.

        Returns:
            The updated policy JSON.
        """
        return policy_json(renew_policy.execute(auth, policy_number))

    @app.get("/policies/{policy_number}/renewal")
    def renewal(
        policy_number: str, auth: AuthContext = Depends(require_auth)
    ) -> dict[str, object]:
        """Return renewal figures.

        Args:
            policy_number: Policy number.
            auth: Verified caller.

        Returns:
            The renewal quote JSON.
        """
        return renewal_json(renewal_details.execute(auth, policy_number))

    @app.get("/policies/{policy_number}/id-card")
    def card(policy_number: str, auth: AuthContext = Depends(require_auth)) -> dict[str, object]:
        """Return an insurance ID card.

        Args:
            policy_number: Policy number.
            auth: Verified caller.

        Returns:
            The ID card JSON.
        """
        return id_card_json(id_card.execute(auth, policy_number))

    @app.get("/documents")
    def documents(
        auth: AuthContext = Depends(require_auth),
        policy_number: str | None = None,
    ) -> dict[str, object]:
        """List documents for the caller.

        Args:
            auth: Verified caller.
            policy_number: Optional policy filter.

        Returns:
            A documents array.
        """
        found = list_documents.execute(auth, policy_number)
        return {"documents": [document_json(item) for item in found]}

    @app.get("/policies/{policy_number}/documents")
    def policy_documents(
        policy_number: str, auth: AuthContext = Depends(require_auth)
    ) -> dict[str, object]:
        """List documents for one policy.

        Args:
            policy_number: Policy number.
            auth: Verified caller.

        Returns:
            A documents array.
        """
        found = list_documents.execute(auth, policy_number)
        return {"documents": [document_json(item) for item in found]}

    @app.get("/documents/{document_id}")
    def download(document_id: str, auth: AuthContext = Depends(require_auth)) -> Response:
        """Download a document.

        Args:
            document_id: Document identifier.
            auth: Verified caller.

        Returns:
            The file body as an attachment.
        """
        document = download_document.execute(auth, document_id)
        return Response(
            content=document.body.encode("utf-8"),
            media_type=document.content_type,
            headers={"Content-Disposition": f'attachment; filename="{document.file_name}"'},
        )

    @app.get("/policies/{policy_number}/vehicles")
    def vehicles(
        policy_number: str, auth: AuthContext = Depends(require_auth)
    ) -> dict[str, object]:
        """List vehicles.

        Args:
            policy_number: Policy number.
            auth: Verified caller.

        Returns:
            A vehicles array.
        """
        return {
            "vehicles": [vehicle_json(item) for item in list_vehicles.execute(auth, policy_number)]
        }

    @app.post("/policies/{policy_number}/vehicles", status_code=201)
    def create_vehicle(
        policy_number: str,
        body: VehicleBody,
        auth: AuthContext = Depends(require_auth),
    ) -> dict[str, object]:
        """Add a vehicle.

        Args:
            policy_number: Policy number.
            body: Vehicle JSON.
            auth: Verified caller.

        Returns:
            The stored vehicle.
        """
        vehicle = add_vehicle.execute(
            auth,
            policy_number,
            NewVehicle(year=body.year, make=body.make, model=body.model, vin=body.vin),
        )
        return vehicle_json(vehicle)

    @app.delete("/policies/{policy_number}/vehicles/{vehicle_id}", status_code=204)
    def delete_vehicle(
        policy_number: str,
        vehicle_id: str,
        auth: AuthContext = Depends(require_auth),
    ) -> Response:
        """Remove a vehicle.

        Args:
            policy_number: Policy number.
            vehicle_id: Vehicle identifier.
            auth: Verified caller.

        Returns:
            An empty 204 response.
        """
        remove_vehicle.execute(auth, policy_number, vehicle_id)
        return Response(status_code=204)

    @app.get("/policies/{policy_number}/drivers")
    def drivers(policy_number: str, auth: AuthContext = Depends(require_auth)) -> dict[str, object]:
        """List drivers.

        Args:
            policy_number: Policy number.
            auth: Verified caller.

        Returns:
            A drivers array.
        """
        found = list_drivers.execute(auth, policy_number)
        return {"drivers": [driver_json(item) for item in found]}

    @app.post("/policies/{policy_number}/drivers", status_code=201)
    def create_driver(
        policy_number: str,
        body: DriverBody,
        auth: AuthContext = Depends(require_auth),
    ) -> dict[str, object]:
        """Add a driver.

        Args:
            policy_number: Policy number.
            body: Driver JSON.
            auth: Verified caller.

        Returns:
            The stored driver.
        """
        try:
            born = date.fromisoformat(body.date_of_birth)
        except ValueError as exc:
            raise InvalidDriver("Date of birth must be an ISO date, such as 1990-01-15.") from exc
        driver = add_driver.execute(
            auth,
            policy_number,
            NewDriver(
                full_name=body.full_name,
                license_number=body.license_number,
                date_of_birth=born,
            ),
        )
        return driver_json(driver)

    @app.delete("/policies/{policy_number}/drivers/{driver_id}", status_code=204)
    def delete_driver(
        policy_number: str,
        driver_id: str,
        auth: AuthContext = Depends(require_auth),
    ) -> Response:
        """Remove a driver.

        Args:
            policy_number: Policy number.
            driver_id: Driver identifier.
            auth: Verified caller.

        Returns:
            An empty 204 response.
        """
        remove_driver.execute(auth, policy_number, driver_id)
        return Response(status_code=204)

    @app.get("/policies/{policy_number}/claims")
    def claims(policy_number: str, auth: AuthContext = Depends(require_auth)) -> dict[str, object]:
        """List claims.

        Args:
            policy_number: Policy number.
            auth: Verified caller.

        Returns:
            A claims array.
        """
        return {"claims": [claim_json(item) for item in list_claims.execute(auth, policy_number)]}

    @app.post("/policies/{policy_number}/claims", status_code=201)
    def create_claim(
        policy_number: str,
        body: ClaimBody,
        auth: AuthContext = Depends(require_auth),
    ) -> dict[str, object]:
        """Submit a claim.

        Args:
            policy_number: Policy number.
            body: Claim JSON.
            auth: Verified caller.

        Returns:
            The stored claim.
        """
        return claim_json(submit_claim.execute(auth, policy_number, body.description))

    return app
