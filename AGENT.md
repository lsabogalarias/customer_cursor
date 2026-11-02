# AGENT.md

Running context for the customer portal proof of concept. Every agent updates this file when it adds, removes, or changes an architectural decision.

## Product

English-language customer portal for auto, truck, and home policies. This repository is a standalone POC. It does not use the D2C Data Gateway or licensee model.

Official remote: `git@github.com:lsabogalarias/customer_cursor.git`.

## Decisions

- Hexagonal services behind one API gateway. The React app calls only the gateway.
- Authentication is email and password. Passwords are stored as Argon2 hashes. A one-hour HMAC JWT authorizes data access.
- `AuthContext` (`user_id`, `email`, `token`) is required on repository methods that read or write a customer's data. Identity credential lookup (`find_by_email`, `add`) runs before a token exists and is the only exception.
- Portal rows are stored in per-service SQLite files. Twilio and card charging are in-memory mocks and do not open network connections.
- Policy numbers are `AUTO-XXXX` or `HOME-XXXX`. Vehicles and drivers are rejected on `HOME-` policies.
- Renewal premium is the current premium plus five percent, rounded half up to cents. It is an illustration, not a carrier rate.
- Money is `Decimal` in Python and a string in JSON.
- Domain packages import the standard library, Pydantic, ports, and `portal_common.identity` only.
- Configuration is read from the environment in each `main.py`. The local default JWT secret is a demo placeholder, not a production secret.
- UI copy, errors, identifiers, and docs are English.
- Startup seed data is inserted by adapters when the SQLite file is empty. Use cases do not seed.

## Layout

- `libs/portal-common`: `AuthContext`, JWT helpers, FastAPI bearer dependency, demo customer ids.
- `services/identity-service`: register, login, current user.
- `services/policy-service`: policies, documents, id cards, renewal, vehicles, drivers, claims.
- `services/billing-service`: payment history and mock pay.
- `services/contact-service`: mock SMS and voice.
- `services/api-gateway`: auth check and reverse proxy.
- `web`: Vite, React, and TypeScript.
- `.cursor/agents`: project subagents used by the orchestrator.

## Seed customer

- User id: `11111111-1111-1111-1111-111111111111`
- Email: `demo.customer@example.com`
- Password: `Demo1234!`
- Policies: `AUTO-1001` (personal auto), `AUTO-2044` (truck), `HOME-3008` (home)

## Log

- 2026-11-02: Repository initialized on `main`.
- 2026-11-02: Added the four services, the gateway, the React portal, unit tests, architecture notes, and the nine project subagents on `poc/customer-portal`. No carrier, Twilio, or payment credentials are stored.
- 2026-11-02: Compliance audit passed. pytest, ruff, and mypy passed. The browser walk covered sign-in, the five menu sections, the ID card, document download, a mock payment, a mock message, and a mock call.
