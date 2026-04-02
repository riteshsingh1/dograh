# Collarx Buyer Guide

This guide helps CodeCanyon buyers deploy, activate, and extend Collarx.

## 1) Product Overview

Collarx is a full-stack voice AI platform with:

- FastAPI backend (`api/`)
- Next.js frontend (`ui/`)
- PostgreSQL + Redis + MinIO
- Telephony providers (Twilio, Vonage, Vobiz, Plivo, Cloudonix, ARI)
- Real-time workflow execution with a visual builder

Core runtime logic is delivered through a private package:

- `collarx-engine` (installed with your access token)

## 2) Requirements

### Infrastructure

- Linux server (recommended 8 GB RAM, 4 vCPU minimum)
- Docker + Docker Compose
- Public domain + TLS certificate
- Ports: `80`, `443`, `3478/udp`, `3478/tcp`, `5349/udp`, `5349/tcp`, TURN relay range

### Accounts

- CodeCanyon purchase code
- Telephony account (Twilio/Vonage/Vobiz/Plivo/etc.)
- Optional AI service accounts (OpenAI, Deepgram, ElevenLabs, etc.)

## 3) Quick Start (15 minutes)

1. Clone your purchased project.
2. Create `.env` based on deployment examples.
3. Add the following required values:
   - `COLLARX_ACCESS_TOKEN`
   - `COLLARX_LICENSE_KEY`
   - `COLLARX_LICENSED_DOMAIN`
   - `COLLARX_LICENSE_SERVER`
4. Build and start:

```bash
docker compose build
docker compose up -d
```

5. Open the UI and verify backend health endpoint.

## 4) License Activation

### Activation flow

1. Go to your license portal URL.
2. Submit your CodeCanyon purchase code and domain.
3. Receive:
   - `COLLARX_LICENSE_KEY`
   - `COLLARX_ACCESS_TOKEN`
4. Add to your `.env` and deploy.

### Domain binding rules

- License key is bound to one domain at activation time.
- Domain mismatch fails runtime validation.
- Domain rebind requires support approval.

### Runtime behavior

- License is validated online with cache + grace period.
- Short outage of license server will not break production immediately.

## 5) Configuration Guide

### Core env vars

- `BACKEND_API_ENDPOINT`
- `DATABASE_URL`
- `REDIS_URL`
- `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET`
- `COLLARX_LICENSE_KEY`, `COLLARX_LICENSED_DOMAIN`, `COLLARX_LICENSE_SERVER`
- `COLLARX_LICENSE_SIGNING_SECRET` (recommended, validates signed responses from license server)
- `COLLARX_ENGINE_SELF_HASH` (optional anti-tamper runtime integrity check)

### Auth mode

- OSS/local: `AUTH_PROVIDER=local`
- Stack Auth: `AUTH_PROVIDER=stack` with Stack credentials

### Telephony config

Set telephony credentials in the app (`/telephony-configurations`) for your provider.

### AI providers

Configure LLM/STT/TTS models under model configuration pages.

## 6) Build Your First Voice Agent

1. Open `Voice Agents` in the sidebar.
2. Create a workflow.
3. Add start node, agent nodes, tools, and end node.
4. Save and test from run/test page.
5. Assign to outbound campaigns or inbound telephony route.

## 7) Campaign Setup

1. Create campaign.
2. Upload/import contacts.
3. Choose workflow and dialing settings.
4. Start campaign and monitor runs in real time.

## 8) Plugin and Integration Extensibility

Collarx supports plugin architecture through `collarx_engine.plugins`:

- `TelephonyPlugin`
- `AIProviderPlugin`
- `WorkflowToolPlugin`
- `IntegrationPlugin`
- `CampaignSourcePlugin`

Plugins are discovered via Python entry points:

```toml
[project.entry-points."collarx.plugins"]
my_plugin = "my_package.plugin:MyPlugin"
```

## 9) Production Deployment

1. Configure reverse proxy and TLS.
2. Configure TURN server (`coturn`) for WebRTC.
3. Set secure secrets.
4. Enable backups for PostgreSQL + MinIO.
5. Add observability (Sentry/Langfuse optional).

## 10) Troubleshooting

### License errors

- Check domain value matches actual deployment domain.
- Verify `COLLARX_LICENSE_SERVER` reachable from backend container.
- Verify key has not been revoked.

### No audio / one-way audio

- Confirm TURN ports open.
- Confirm telephony webhook and websocket endpoints reachable.

### Campaign not dialing

- Check provider credentials.
- Check org concurrency limits and quotas.

## 11) Support and Updates

- Product updates are released through version tags.
- Pin your deployment to a known working version.
- Keep release notes and changelog in your deployment runbook.
