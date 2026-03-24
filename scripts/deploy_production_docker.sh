#!/usr/bin/env bash
set -euo pipefail

# Production deploy script for self-hosted Ubuntu server.
# - Builds API/UI from your current repo changes
# - Starts core Docker services with docker-compose.yaml
# - Runs Alembic migrations in api container
# - Optionally configures host Nginx reverse proxy
#
# Usage:
#   bash scripts/deploy_production_docker.sh \
#     --domain app.example.com \
#     --backend-endpoint https://app.example.com \
#     --configure-nginx
#
# Optional:
#   --app-dir /opt/dograh
#   --include-coturn
#   --skip-migrations

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOMAIN=""
BACKEND_ENDPOINT=""
CONFIGURE_NGINX=false
INCLUDE_COTURN=false
SKIP_MIGRATIONS=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --app-dir)
      APP_DIR="$2"; shift 2 ;;
    --domain)
      DOMAIN="$2"; shift 2 ;;
    --backend-endpoint)
      BACKEND_ENDPOINT="$2"; shift 2 ;;
    --configure-nginx)
      CONFIGURE_NGINX=true; shift ;;
    --include-coturn)
      INCLUDE_COTURN=true; shift ;;
    --skip-migrations)
      SKIP_MIGRATIONS=true; shift ;;
    *)
      echo "Unknown arg: $1"
      exit 1 ;;
  esac
done

cd "$APP_DIR"

if [[ ! -f "docker-compose.yaml" ]]; then
  echo "docker-compose.yaml not found in $APP_DIR"
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed"
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose plugin is not available"
  exit 1
fi

ENV_FILE=".env.production"
if [[ ! -f "$ENV_FILE" ]]; then
  cat > "$ENV_FILE" <<'EOF'
# Copy/edit before deployment
REGISTRY=ghcr.io/dograh-hq
ENABLE_TELEMETRY=false
BACKEND_API_ENDPOINT=https://your-domain.example.com
BACKEND_URL=http://api:8000
TURN_HOST=
TURN_SECRET=
OSS_JWT_SECRET=ChangeMeInProduction
EOF
  echo "Created $ENV_FILE template. Update it and rerun."
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

if [[ -n "$BACKEND_ENDPOINT" ]]; then
  export BACKEND_API_ENDPOINT="$BACKEND_ENDPOINT"
fi

if [[ -z "${BACKEND_API_ENDPOINT:-}" ]]; then
  echo "BACKEND_API_ENDPOINT is required (set in .env.production or --backend-endpoint)"
  exit 1
fi

if [[ "${OSS_JWT_SECRET:-}" == "ChangeMeInProduction" || -z "${OSS_JWT_SECRET:-}" ]]; then
  echo "Set a secure OSS_JWT_SECRET in $ENV_FILE before production deploy."
  exit 1
fi

OVERRIDE_FILE="docker-compose.prod.override.yml"
cat > "$OVERRIDE_FILE" <<'EOF'
services:
  api:
    build:
      context: .
      dockerfile: api/Dockerfile
    image: dograh-api:prod-local
    environment:
      ENVIRONMENT: "production"
      LOG_LEVEL: "INFO"
    restart: unless-stopped

  ui:
    build:
      context: .
      dockerfile: ui/Dockerfile
    image: dograh-ui:prod-local
    environment:
      NODE_ENV: "production"
    restart: unless-stopped

  postgres:
    restart: unless-stopped
  redis:
    restart: unless-stopped
  minio:
    restart: unless-stopped
  cloudflared:
    restart: unless-stopped
EOF

COMPOSE_ARGS=(-f docker-compose.yaml -f "$OVERRIDE_FILE" --env-file "$ENV_FILE")

echo "Pulling base images..."
docker compose "${COMPOSE_ARGS[@]}" pull postgres redis minio cloudflared || true

echo "Building API/UI with your changes..."
docker compose "${COMPOSE_ARGS[@]}" build --pull api ui

echo "Starting core services..."
docker compose "${COMPOSE_ARGS[@]}" up -d postgres redis minio cloudflared api ui

if [[ "$INCLUDE_COTURN" == "true" ]]; then
  echo "Starting coturn service..."
  docker compose "${COMPOSE_ARGS[@]}" --profile remote up -d coturn
fi

if [[ "$SKIP_MIGRATIONS" != "true" ]]; then
  echo "Running database migrations..."
  docker compose "${COMPOSE_ARGS[@]}" exec -T api alembic -c /app/api/alembic.ini upgrade head
fi

echo "Waiting for API health..."
for i in {1..40}; do
  if curl -fsS "http://127.0.0.1:8000/api/v1/health" >/dev/null 2>&1; then
    echo "API is healthy."
    break
  fi
  if [[ "$i" -eq 40 ]]; then
    echo "API health check failed."
    docker compose "${COMPOSE_ARGS[@]}" ps
    exit 1
  fi
  sleep 3
done

echo "Waiting for UI health..."
for i in {1..40}; do
  if curl -fsS "http://127.0.0.1:3010" >/dev/null 2>&1; then
    echo "UI is healthy."
    break
  fi
  if [[ "$i" -eq 40 ]]; then
    echo "UI health check failed."
    docker compose "${COMPOSE_ARGS[@]}" ps
    exit 1
  fi
  sleep 3
done

if [[ "$CONFIGURE_NGINX" == "true" ]]; then
  if [[ -z "$DOMAIN" ]]; then
    echo "--configure-nginx requires --domain"
    exit 1
  fi

  NGINX_CONF="/etc/nginx/sites-available/dograh.conf"
  echo "Writing host Nginx config to $NGINX_CONF"
  sudo tee "$NGINX_CONF" >/dev/null <<EOF
server {
    listen 80;
    server_name ${DOMAIN};

    client_max_body_size 100M;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /voice-audio/ {
        proxy_pass http://127.0.0.1:9000/voice-audio/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
    }

    location / {
        proxy_pass http://127.0.0.1:3010;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

  sudo ln -sfn "$NGINX_CONF" /etc/nginx/sites-enabled/dograh.conf
  sudo nginx -t
  sudo systemctl reload nginx
  echo "Nginx reloaded for domain: $DOMAIN"
fi

echo ""
echo "Deployment complete."
echo "Compose status:"
docker compose "${COMPOSE_ARGS[@]}" ps
echo ""
echo "Useful commands:"
echo "  docker compose ${COMPOSE_ARGS[*]} logs -f api ui"
echo "  docker compose ${COMPOSE_ARGS[*]} restart api ui"
