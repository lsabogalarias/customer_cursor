"""Composition root for the policy service."""

import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from portal_common.fastapi_auth import build_require_auth

from policy_service.adapters.http import create_app
from policy_service.adapters.sqlite_policy import SqlitePolicyRepository
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


def build_app() -> FastAPI:
    """Wire adapters and use cases.

    Returns:
        The policy FastAPI application.

    Environment variables:
        JWT_SECRET: HMAC secret. Defaults to the local demo placeholder.
        DATABASE_PATH: SQLite file. Defaults to ``data/policy.db``.
    """
    secret = os.environ.get("JWT_SECRET", "dev-only-change-me")
    database_path = Path(
        os.environ.get(
            "DATABASE_PATH",
            str(Path(__file__).resolve().parents[2] / "data" / "policy.db"),
        )
    )
    policies = SqlitePolicyRepository(database_path)
    policies.seed_demo()
    return create_app(
        list_policies=ListPolicies(policies),
        get_policy=GetPolicy(policies),
        renew_policy=RenewPolicy(policies),
        renewal_details=GetRenewalDetails(policies),
        id_card=GetIdCard(policies),
        list_documents=ListDocuments(policies),
        download_document=DownloadDocument(policies),
        list_vehicles=ListVehicles(policies),
        add_vehicle=AddVehicle(policies),
        remove_vehicle=RemoveVehicle(policies),
        list_drivers=ListDrivers(policies),
        add_driver=AddDriver(policies),
        remove_driver=RemoveDriver(policies),
        submit_claim=SubmitClaim(policies),
        list_claims=ListClaims(policies),
        require_auth=build_require_auth(secret),
    )


app = build_app()


def main() -> None:
    """Serve the policy API.

    Environment variables:
        PORT: Listen port. Defaults to 8002.
    """
    port = int(os.environ.get("PORT", "8002"))
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
