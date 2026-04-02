# Collarx License Server

FastAPI service for purchase-code activation, domain-bound validation, and admin controls.

## Run

```bash
cd collarx-license-server
uv run uvicorn app.main:app --reload --port 8090
```

## Required env vars

- `DATABASE_URL` (defaults to local sqlite)
- `ENVATO_TOKEN` (optional; when set, purchase codes are verified against Envato API)
- `COLLARX_LICENSE_ADMIN_KEY` (required for admin create/revoke endpoints)
- `COLLARX_LICENSE_ADMIN_USERNAME` and `COLLARX_LICENSE_ADMIN_PASSWORD` (admin UI login)
- `COLLARX_LICENSE_SESSION_SECRET` (session cookie signing)
- `COLLARX_LICENSE_SIGNING_SECRET` (HMAC signature for validation responses)
