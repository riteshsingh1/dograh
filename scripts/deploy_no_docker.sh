#!/usr/bin/env bash
set -euo pipefail

# Non-Docker deployment/start script for local or VM environments.
# Starts backend services + frontend, and (optionally) cloudflared tunnel.

BASE_DIR="$(cd "$(dirname "$(dirname "${BASH_SOURCE[0]}")")" && pwd)"
RUN_DIR="$BASE_DIR/run"
LOG_DIR="$BASE_DIR/logs/no_docker"
BACKEND_ENV_FILE="$BASE_DIR/api/.env"
UI_ENV_FILE="$BASE_DIR/ui/.env"
VENV_PATH="$BASE_DIR/venv"

mkdir -p "$RUN_DIR" "$LOG_DIR"

MODE="${1:-dev}" # dev or prod

echo "Starting Dograh without Docker (mode=$MODE)"
echo "Base directory: $BASE_DIR"

if [[ ! -f "$BACKEND_ENV_FILE" ]]; then
  echo "Missing $BACKEND_ENV_FILE"
  echo "Create it from api/.env.example first."
  exit 1
fi

if [[ ! -f "$UI_ENV_FILE" ]]; then
  echo "Missing $UI_ENV_FILE"
  echo "Create ui/.env before running this script."
  exit 1
fi

set -a
source "$BACKEND_ENV_FILE"
set +a

if [[ -d "$VENV_PATH" && -f "$VENV_PATH/bin/activate" ]]; then
  source "$VENV_PATH/bin/activate"
else
  echo "Python venv not found at $VENV_PATH"
  echo "Create one and install dependencies:"
  echo "  python3 -m venv venv && source venv/bin/activate && pip install -r api/requirements.txt"
  exit 1
fi

pushd "$BASE_DIR" >/dev/null

echo "Running DB migrations..."
alembic -c "$BASE_DIR/api/alembic.ini" upgrade head

echo "Starting backend services..."
if pgrep -f "scripts/start_services_dev.sh" >/dev/null 2>&1; then
  echo "Backend start script appears to already be running, skipping duplicate start."
else
  nohup bash scripts/start_services_dev.sh >"$LOG_DIR/backend_supervisor.log" 2>&1 &
  echo $! >"$RUN_DIR/deploy_no_docker_backend.pid"
fi

echo "Installing frontend dependencies..."
pushd "$BASE_DIR/ui" >/dev/null
npm install

if [[ "$MODE" == "prod" ]]; then
  echo "Building frontend..."
  npm run build
  echo "Starting frontend in production mode..."
  nohup npm run start >"$LOG_DIR/ui.log" 2>&1 &
else
  echo "Starting frontend in development mode..."
  nohup npm run dev >"$LOG_DIR/ui.log" 2>&1 &
fi
echo $! >"$RUN_DIR/deploy_no_docker_ui.pid"
popd >/dev/null

if command -v cloudflared >/dev/null 2>&1; then
  if [[ "${START_CLOUDFLARED:-true}" == "true" ]]; then
    if pgrep -f "cloudflared.*--metrics 0.0.0.0:2000" >/dev/null 2>&1; then
      echo "cloudflared with metrics already running, skipping."
    else
      echo "Starting cloudflared tunnel (for telephony webhooks)..."
      nohup cloudflared tunnel --url "http://127.0.0.1:8000" --metrics 0.0.0.0:2000 \
        >"$LOG_DIR/cloudflared.log" 2>&1 &
      echo $! >"$RUN_DIR/deploy_no_docker_cloudflared.pid"
    fi
  else
    echo "Skipping cloudflared start (START_CLOUDFLARED=false)."
  fi
else
  echo "cloudflared not found; telephony providers like Twilio need a public BACKEND_API_ENDPOINT."
fi

popd >/dev/null

echo
echo "Deployment started."
echo "- Backend logs: $LOG_DIR/backend_supervisor.log"
echo "- UI logs:      $LOG_DIR/ui.log"
echo "- Tunnel logs:  $LOG_DIR/cloudflared.log (if started)"
echo
echo "Tip: export BACKEND_API_ENDPOINT to your public tunnel/domain for Twilio callbacks."
