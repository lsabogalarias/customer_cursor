# AGENT.md

Running context for the customer portal proof of concept. Every agent updates this file when it adds, removes, or changes an architectural decision.

## Product

English-language customer portal for auto, truck, and home policies. This repository is a standalone POC. It does not use the D2C Data Gateway or licensee model.

Official remote: `git@github.com:lsabogalarias/customer_cursor.git`.

## Decisions

- Hexagonal services behind one API gateway. The React app calls only the gateway.
- Authentication is email and password. Passwords are stored as Argon2 hashes. A short-lived HMAC JWT authorizes data access.
- `AuthContext` (`user_id`, `email`, `token`) is required on repository methods that read or write a customer's data. Identity credential lookup runs before a token exists and is the only exception.
- Portal rows are stored in SQLite. Twilio and card charging are in-memory mocks and do not open network connections.
- Policy numbers are `AUTO-XXXX` or `HOME-XXXX`. Vehicles and drivers are rejected on `HOME-` policies.
- Money is `Decimal` in Python and a string in JSON.
- UI copy, errors, identifiers, and docs are English.

## Log

- 2026-11-02: Repository initialized on `main` with project context. Service and UI implementation follows on `poc/customer-portal`.
