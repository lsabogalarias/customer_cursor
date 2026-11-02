# Customer Portal POC

Local proof of concept for an insurance customer portal. Customers sign in with email and password, then review auto, truck, and home policies, documents, payments, and contact their agent.

The browser talks only to the API gateway. Identity, policy, billing, and contact are separate FastAPI services in hexagonal form. Twilio and the payment gateway are mocks and never call the network.

Demo customer: `demo.customer@example.com` / `Demo1234!`

See [AGENT.md](AGENT.md) for decisions and [docs/architecture.md](docs/architecture.md) for the service map.

## Run locally

Python 3.11+ and Node 20+ are required.

```bash
chmod +x scripts/*.sh
./scripts/bootstrap.sh
./scripts/run-backend.sh
```

In another terminal:

```bash
cd web
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. The Vite dev server proxies `/api` to the gateway on port 8000.

| Process | Port |
|---|---|
| API gateway | 8000 |
| Identity | 8001 |
| Policy | 8002 |
| Billing | 8003 |
| Contact | 8004 |
| Web | 5173 |

`JWT_SECRET` defaults to `dev-only-change-me` for this local demo. Do not reuse it outside this POC.

## Tests

```bash
./scripts/test.sh
```

That runs pytest, ruff, and mypy in each Python project.
