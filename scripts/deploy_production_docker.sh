#!/usr/bin/env bash
set -euo pipefail

# Production deploy script for self-hosted Ubuntu server.
# - Builds API/UI from your current repo changes
# - Starts core Docker services with docker-compose.yaml
# - Runs Alembic migrations in api container
# - Optionally configures host Nginx reverse proxy
# - Optionally provisions HTTPS certs via Certbot
#
# Usage:
#   bash scripts/deploy_production_docker.sh \
#     --domain app.example.com \
#     --api-domain api.example.com \
#     --backend-endpoint https://app.example.com \
#     --configure-nginx \
#     --enable-https \
#     --certbot-email ops@example.com \
#     --api-port 8001 \
#     --ui-port 3011
#
# Optional:
#   --app-dir /opt/dograh
#   --include-coturn
#   --skip-migrations
#   --minio-port 9002

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOMAIN=""
API_DOMAIN=""
BACKEND_ENDPOINT=""
CONFIGURE_NGINX=false
ENABLE_HTTPS=false
INCLUDE_COTURN=false
SKIP_MIGRATIONS=false
CERTBOT_EMAIL=""
HOST_API_PORT="${HOST_API_PORT:-8000}"
HOST_UI_PORT="${HOST_UI_PORT:-3010}"
HOST_MINIO_PORT="${HOST_MINIO_PORT:-9000}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --app-dir)
      APP_DIR="$2"; shift 2 ;;
    --domain)
      DOMAIN="$2"; shift 2 ;;
    --api-domain)
      API_DOMAIN="$2"; shift 2 ;;
    --backend-endpoint)
      BACKEND_ENDPOINT="$2"; shift 2 ;;
    --configure-nginx)
      CONFIGURE_NGINX=true; shift ;;
    --enable-https)
      ENABLE_HTTPS=true; shift ;;
    --certbot-email)
      CERTBOT_EMAIL="$2"; shift 2 ;;
    --include-coturn)
      INCLUDE_COTURN=true; shift ;;
    --skip-migrations)
      SKIP_MIGRATIONS=true; shift ;;
    --api-port)
      HOST_API_PORT="$2"; shift 2 ;;
    --ui-port)
      HOST_UI_PORT="$2"; shift 2 ;;
    --minio-port)
      HOST_MINIO_PORT="$2"; shift 2 ;;
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
CERTBOT_EMAIL=ops@example.com
HOST_API_PORT=8000
HOST_UI_PORT=3010
HOST_MINIO_PORT=9000
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
cat > "$OVERRIDE_FILE" <<EOF
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
    ports:
      - "${HOST_API_PORT}:8000"

  ui:
    build:
      context: .
      dockerfile: ui/Dockerfile
    image: dograh-ui:prod-local
    environment:
      NODE_ENV: "production"
    restart: unless-stopped
    ports:
      - "${HOST_UI_PORT}:3010"

  postgres:
    restart: unless-stopped
  redis:
    restart: unless-stopped
  minio:
    restart: unless-stopped
    ports:
      - "127.0.0.1:${HOST_MINIO_PORT}:9000"
      - "127.0.0.1:9001:9001"
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
  if curl -fsS "http://127.0.0.1:${HOST_API_PORT}/api/v1/health" >/dev/null 2>&1; then
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
  if curl -fsS "http://127.0.0.1:${HOST_UI_PORT}" >/dev/null 2>&1; then
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
  API_SERVER_NAME="${API_DOMAIN:-$DOMAIN}"
  sudo tee "$NGINX_CONF" >/dev/null <<EOF
server {
    listen 80;
    server_name ${DOMAIN};

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:${HOST_UI_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

server {
    listen 80;
    server_name ${API_SERVER_NAME};

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:${HOST_API_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /voice-audio/ {
        proxy_pass http://127.0.0.1:${HOST_MINIO_PORT}/voice-audio/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
    }
}
EOF

  sudo ln -sfn "$NGINX_CONF" /etc/nginx/sites-enabled/dograh.conf
  sudo nginx -t
  sudo systemctl reload nginx
  echo "Nginx reloaded for ui domain: $DOMAIN and api domain: ${API_SERVER_NAME}"
fi

if [[ "$ENABLE_HTTPS" == "true" ]]; then
  if [[ "$CONFIGURE_NGINX" != "true" ]]; then
    echo "--enable-https requires --configure-nginx in the same run."
    exit 1
  fi
  if [[ -z "$DOMAIN" ]]; then
    echo "--enable-https requires --domain"
    exit 1
  fi

  if [[ -z "$CERTBOT_EMAIL" ]]; then
    echo "Set CERTBOT_EMAIL in .env.production or pass --certbot-email"
    exit 1
  fi

  if ! command -v certbot >/dev/null 2>&1; then
    echo "Installing certbot and nginx plugin..."
    sudo apt-get update -y
    sudo apt-get install -y certbot python3-certbot-nginx
  fi

  CERTBOT_DOMAINS=(-d "$DOMAIN")
  if [[ "$API_SERVER_NAME" != "$DOMAIN" ]]; then
    CERTBOT_DOMAINS+=(-d "$API_SERVER_NAME")
  fi

  echo "Provisioning HTTPS certificates via certbot..."
  sudo certbot --nginx \
    --non-interactive \
    --agree-tos \
    --redirect \
    --keep-until-expiring \
    -m "$CERTBOT_EMAIL" \
    "${CERTBOT_DOMAINS[@]}"

  if systemctl list-unit-files 2>/dev/null | grep -q "^certbot\.timer"; then
    sudo systemctl enable --now certbot.timer >/dev/null 2>&1 || true
  fi

  sudo nginx -t
  sudo systemctl reload nginx
  echo "HTTPS enabled for: $DOMAIN ${API_SERVER_NAME}"
fi

echo ""
echo "Deployment complete."
echo "Ports: api=${HOST_API_PORT}, ui=${HOST_UI_PORT}, minio=${HOST_MINIO_PORT}"
echo "Compose status:"
docker compose "${COMPOSE_ARGS[@]}" ps
echo ""
echo "Useful commands:"
echo "  docker compose ${COMPOSE_ARGS[*]} logs -f api ui"
echo "  docker compose ${COMPOSE_ARGS[*]} restart api ui"
