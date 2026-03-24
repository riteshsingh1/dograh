#!/usr/bin/env bash
set -euo pipefail

# Quick redeploy wrapper for production Docker deployment.
# Reuses .env.production and calls deploy_production_docker.sh.
#
# Usage:
#   bash scripts/redeploy_production_docker.sh --pull
#   bash scripts/redeploy_production_docker.sh --with-nginx --domain va.example.com --api-domain api.example.com
#   bash scripts/redeploy_production_docker.sh --with-https --certbot-email ops@example.com

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOY_SCRIPT="$APP_DIR/scripts/deploy_production_docker.sh"
ENV_FILE="$APP_DIR/.env.production"

DO_PULL=false
WITH_NGINX=false
WITH_HTTPS=false
SKIP_MIGRATIONS=false
INCLUDE_COTURN=false
CLI_DOMAIN=""
CLI_API_DOMAIN=""
CLI_CERTBOT_EMAIL=""
CLI_API_PORT=""
CLI_UI_PORT=""
CLI_MINIO_PORT=""
CLI_BACKEND_ENDPOINT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pull)
      DO_PULL=true; shift ;;
    --with-nginx)
      WITH_NGINX=true; shift ;;
    --with-https)
      WITH_HTTPS=true; WITH_NGINX=true; shift ;;
    --skip-migrations)
      SKIP_MIGRATIONS=true; shift ;;
    --include-coturn)
      INCLUDE_COTURN=true; shift ;;
    --domain)
      CLI_DOMAIN="$2"; shift 2 ;;
    --api-domain)
      CLI_API_DOMAIN="$2"; shift 2 ;;
    --certbot-email)
      CLI_CERTBOT_EMAIL="$2"; shift 2 ;;
    --backend-endpoint)
      CLI_BACKEND_ENDPOINT="$2"; shift 2 ;;
    --api-port)
      CLI_API_PORT="$2"; shift 2 ;;
    --ui-port)
      CLI_UI_PORT="$2"; shift 2 ;;
    --minio-port)
      CLI_MINIO_PORT="$2"; shift 2 ;;
    *)
      echo "Unknown arg: $1"
      exit 1 ;;
  esac
done

cd "$APP_DIR"

if [[ ! -x "$DEPLOY_SCRIPT" ]]; then
  chmod +x "$DEPLOY_SCRIPT"
fi

if [[ -f "$ENV_FILE" ]]; then
  set -a
  source "$ENV_FILE"
  set +a
fi

DOMAIN="${CLI_DOMAIN:-${DOMAIN:-}}"
API_DOMAIN="${CLI_API_DOMAIN:-${API_DOMAIN:-}}"
CERTBOT_EMAIL="${CLI_CERTBOT_EMAIL:-${CERTBOT_EMAIL:-}}"
API_PORT="${CLI_API_PORT:-${HOST_API_PORT:-}}"
UI_PORT="${CLI_UI_PORT:-${HOST_UI_PORT:-}}"
MINIO_PORT="${CLI_MINIO_PORT:-${HOST_MINIO_PORT:-}}"
BACKEND_ENDPOINT="${CLI_BACKEND_ENDPOINT:-${BACKEND_API_ENDPOINT:-}}"

if [[ "$DO_PULL" == "true" ]]; then
  git fetch --all --prune
  git pull --ff-only
fi

DEPLOY_ARGS=()

if [[ -n "$BACKEND_ENDPOINT" ]]; then
  DEPLOY_ARGS+=(--backend-endpoint "$BACKEND_ENDPOINT")
fi
if [[ -n "$API_PORT" ]]; then
  DEPLOY_ARGS+=(--api-port "$API_PORT")
fi
if [[ -n "$UI_PORT" ]]; then
  DEPLOY_ARGS+=(--ui-port "$UI_PORT")
fi
if [[ -n "$MINIO_PORT" ]]; then
  DEPLOY_ARGS+=(--minio-port "$MINIO_PORT")
fi
if [[ "$SKIP_MIGRATIONS" == "true" ]]; then
  DEPLOY_ARGS+=(--skip-migrations)
fi
if [[ "$INCLUDE_COTURN" == "true" ]]; then
  DEPLOY_ARGS+=(--include-coturn)
fi

if [[ "$WITH_NGINX" == "true" ]]; then
  if [[ -z "$DOMAIN" ]]; then
    echo "--with-nginx requires --domain (or DOMAIN in .env.production)"
    exit 1
  fi
  DEPLOY_ARGS+=(--configure-nginx --domain "$DOMAIN")
  if [[ -n "$API_DOMAIN" ]]; then
    DEPLOY_ARGS+=(--api-domain "$API_DOMAIN")
  fi
fi

if [[ "$WITH_HTTPS" == "true" ]]; then
  if [[ -z "$CERTBOT_EMAIL" ]]; then
    echo "--with-https requires --certbot-email (or CERTBOT_EMAIL in .env.production)"
    exit 1
  fi
  DEPLOY_ARGS+=(--enable-https --certbot-email "$CERTBOT_EMAIL")
fi

echo "Running redeploy with args: ${DEPLOY_ARGS[*]}"
bash "$DEPLOY_SCRIPT" "${DEPLOY_ARGS[@]}"
