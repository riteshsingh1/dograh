# Deployment and Integration Handover (Client-Hosted)

Use this document as the deployment and integration handover for a client-hosted Collarax setup.

---

## 1) Project Information

- **Client Name:** `<client_name>`
- **Project Name:** `<project_name>`
- **Environment:** `Production / Staging`
- **Deployment Date:** `<yyyy-mm-dd>`
- **Prepared By:** `Ritesh Singh`
- **Client Technical Owner:** `Ritesh Singh`

---

## 2) Services Required on Client Server

### Core Services (Mandatory)

| Service | Purpose | Required |
|---|---|---|
| `ui` | Next.js frontend application | Yes |
| `api` | FastAPI backend application | Yes |
| `postgres` | Primary database (pgvector/PostgreSQL) | Yes |
| `redis` | Cache and background queue support | Yes |
| `minio` | Object storage for recordings/files | Yes |

### Remote Production Services

| Service | Purpose | Required |
|---|---|---|
| `nginx` | HTTPS termination + reverse proxy | Yes |
| `coturn` | TURN/STUN server for WebRTC voice calls | Yes |

### Optional Services

| Service | Purpose | Required |
|---|---|---|
| `cloudflared` | Tunnel/metrics flow (if used by deployment design) | Optional |
| `Langfuse` | Tracing/observability | Optional |
| `Sentry` | Error monitoring | Optional |

---

## 3) Client Infrastructure Requirements

### Server Requirements

- Linux server with Docker and Docker Compose installed
- Recommended baseline: **8 GB RAM**, **4 vCPU**
- Persistent disk for Postgres and MinIO data
- Public IP (or domain mapped to server)

### Network and Firewall Requirements

Open the following ports to the internet:

- `80/tcp` - HTTP (redirect/challenges)
- `443/tcp` - HTTPS
- `3478/tcp`, `3478/udp` - TURN/STUN
- `5349/tcp`, `5349/udp` - TURN over TLS
- `49152-49200/udp` - TURN media relay range

### DNS and SSL Requirements

- DNS A record pointing domain/subdomain to server IP
- SSL strategy:
  - Initial setup: self-signed certificate (for validation/testing), or
  - Production: public trusted certificate (recommended, e.g. Let's Encrypt)

---

## 4) Integration Inputs Required from Client

Collect and validate the following before go-live.

### A. Security and Ownership

- Security/Compliance owner name and contact
- Incident/on-call contact
- Backup owner and retention expectations
- Certificate renewal owner

### B. Mandatory Application Secrets

- `OSS_JWT_SECRET` (strong random value)
- `DATABASE_URL` (or DB host/user/password/db name inputs)
- `REDIS_URL` (or Redis host/password/port inputs)
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `MINIO_BUCKET` (default commonly `voice-audio`)
- `TURN_HOST`
- `TURN_SECRET`

### C. Telephony Provider Credentials (Choose One)

#### Twilio

- Account SID
- Auth Token
- Phone number(s) enabled for voice
- Webhook approval from client network/security team

#### Vonage

- Application ID
- Private Key
- API Key/API Secret (if used)
- Phone number(s)

#### Custom Telephony/SIP Provider

- API authentication details
- Webhook authentication/signature specification
- Audio transport format expectations

### D. Optional Integrations

- Langfuse keys and host (`LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`)
- Sentry DSN (`SENTRY_DSN`)
- AWS S3 details if replacing MinIO (`ENABLE_AWS_S3=true`, bucket, region)

---

## 5) Environment Variables Checklist

Mark each as provided/configured.

| Variable | Provided by Client | Configured in Deployment | Notes |
|---|---|---|---|
| `ENVIRONMENT` | [ ] | [ ] | `production` recommended |
| `DEPLOYMENT_MODE` | [ ] | [ ] | `oss` for self-hosted |
| `AUTH_PROVIDER` | [ ] | [ ] | `local` for OSS |
| `BACKEND_API_ENDPOINT` | [ ] | [ ] | Public backend URL |
| `DATABASE_URL` | [ ] | [ ] | Required |
| `REDIS_URL` | [ ] | [ ] | Required |
| `OSS_JWT_SECRET` | [ ] | [ ] | Required, strong secret |
| `MINIO_ENDPOINT` | [ ] | [ ] | Required for MinIO |
| `MINIO_ACCESS_KEY` | [ ] | [ ] | Required |
| `MINIO_SECRET_KEY` | [ ] | [ ] | Required |
| `MINIO_BUCKET` | [ ] | [ ] | Required |
| `MINIO_SECURE` | [ ] | [ ] | `true` for HTTPS endpoint |
| `TURN_HOST` | [ ] | [ ] | Required for WebRTC |
| `TURN_SECRET` | [ ] | [ ] | Required for WebRTC |
| `ENABLE_TRACING` | [ ] | [ ] | Optional |
| `LANGFUSE_HOST` | [ ] | [ ] | Optional |
| `LANGFUSE_PUBLIC_KEY` | [ ] | [ ] | Optional |
| `LANGFUSE_SECRET_KEY` | [ ] | [ ] | Optional |
| `SENTRY_DSN` | [ ] | [ ] | Optional |
| `ENABLE_TELEMETRY` | [ ] | [ ] | Client preference |

---

## 6) Deployment and Validation Checklist

### Pre-Deployment

- [ ] Server provisioned and hardened
- [ ] Docker + Docker Compose installed
- [ ] Required ports open in firewall/security groups
- [ ] DNS configured (if custom domain)
- [ ] SSL certificate plan confirmed
- [ ] All secrets securely shared

### Deployment

- [ ] Compose stack started successfully
- [ ] All containers healthy
- [ ] UI accessible over HTTPS
- [ ] API health endpoint returns healthy status
- [ ] TURN connectivity validated

### Functional Validation

- [ ] User login works
- [ ] Workflow creation works
- [ ] Outbound call test successful
- [ ] Inbound call test successful (if enabled)
- [ ] Recording/file upload and retrieval works

### Post-Deployment

- [ ] Backup jobs configured and tested
- [ ] Monitoring/alerts configured
- [ ] Logs centralized or retained per policy
- [ ] Runbook shared with client team
- [ ] UAT sign-off received

---

## 7) Handover Deliverables

- [ ] Deployment architecture overview
- [ ] Docker Compose and env template files
- [ ] Telephony setup runbook (provider-specific)
- [ ] SSL/DNS runbook
- [ ] Operations runbook (restart, logs, backup, restore, rollback)
- [ ] Support and escalation matrix

---

## 8) Support Contacts

| Role | Name | Contact | Availability |
|---|---|---|---|
| Implementation Owner | `<name>` | `<email/phone>` | `<hours>` |
| DevOps Owner | `<name>` | `<email/phone>` | `<hours>` |
| Client Technical Owner | `<name>` | `<email/phone>` | `<hours>` |

---

## 9) Sign-Off

By signing below, both teams confirm that deployment prerequisites, integrations, and operational handover are complete.

- **Service Provider Representative:** `<name>`  
  **Signature:** `<signature>`  
  **Date:** `<yyyy-mm-dd>`

- **Client Representative:** `<name>`  
  **Signature:** `<signature>`  
  **Date:** `<yyyy-mm-dd>`

