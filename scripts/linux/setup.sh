#!/usr/bin/env bash
# =============================================================================
# setup.sh — One-time environment setup on the VPS
#
# Usage:
#   chmod +x scripts/linux/setup.sh
#   ./scripts/linux/setup.sh
#
# What it does:
#   1. Checks Python 3.9
#   2. Creates the virtualenv and installs dependencies
#   3. Creates and registers the systemd service (if not already registered)
#   4. Starts the service
#
# Requirements:
#   - Python 3.9 installed on the VPS (python3.9)
#   - Run from the project root
#   - sudo privileges (needed for systemd)
# =============================================================================

set -euo pipefail

# Always run from the project root (2 levels up from this script)
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

VENV_DIR=".venv"
REQUIREMENTS="requirements.txt"
HASH_FILE=".requirements.hash"
ENV_FILE=".env"

SERVICE_NAME="optimus-api"                                       # ← change to your preferred service name
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
PROJECT_DIR="$PWD"                                               # absolute path to project root (resolved after cd)
SERVICE_USER="${SUDO_USER:-opc}"                                  # user that will run gunicorn

# ─── Output colors ───────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${GREEN}[optimus:setup]${NC} $1"; }
warn()    { echo -e "${YELLOW}[optimus:setup]${NC} $1"; }
error()   { echo -e "${RED}[optimus:setup] $1${NC}"; exit 1; }

# ─── Check Python 3.9 ───────────────────────────────────────────────────────
info "Checking Python 3.9..."
if ! command -v python3.9 &>/dev/null; then
    error "python3.9 not found. Install it with: sudo dnf install python3.9 -y"
fi
python3.9 --version

# ─── Create virtualenv ───────────────────────────────────────────────────────
if [ -d "$VENV_DIR" ]; then
    warn "Virtualenv '$VENV_DIR' already exists. Skipping creation."
else
    info "Creating virtualenv in $VENV_DIR with Python 3.9..."
    python3.9 -m venv "$VENV_DIR"
    info "Virtualenv created."
fi

# ─── Activate virtualenv ─────────────────────────────────────────────────────
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# ─── Install / update dependencies ───────────────────────────────────────────
info "Upgrading pip..."
pip install --upgrade pip --quiet

info "Installing dependencies from $REQUIREMENTS..."
pip install -r "$REQUIREMENTS"

# Save hash so deploy.sh can detect changes later
sha256sum "$REQUIREMENTS" > "$HASH_FILE"
info "Requirements hash saved to $HASH_FILE"

# ─── Check .env ────────────────────────────────────────────────────────────
if [ ! -f "$ENV_FILE" ]; then
    warn ".env not found. The service will start without environment variables."
    warn "Create it manually: nano ${PROJECT_DIR}/.env"
else
    info ".env found."
fi

# ─── Create / overwrite systemd service (always regenerated to keep paths correct) ───
info "Writing systemd service '$SERVICE_NAME' at $SERVICE_FILE ..."
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=${SERVICE_NAME}
After=network.target

[Service]
User=${SERVICE_USER}
WorkingDirectory=${PROJECT_DIR}
EnvironmentFile=-${PROJECT_DIR}/.env
ExecStart=${PROJECT_DIR}/.venv/bin/gunicorn app.main:app \\
    -w 2 -k uvicorn.workers.UvicornWorker \\
    --bind 127.0.0.1:8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
info "Service '$SERVICE_NAME' registered and enabled."

# ─── Start the service ────────────────────────────────────────────────────────
if systemctl is-active --quiet "$SERVICE_NAME"; then
    warn "Service '$SERVICE_NAME' is already running. Skipping start."
else
    info "Starting service '$SERVICE_NAME'..."
    sudo systemctl start "$SERVICE_NAME"
    sleep 2

    if systemctl is-active --quiet "$SERVICE_NAME"; then
        info "Service '$SERVICE_NAME' is running."
    else
        error "Service '$SERVICE_NAME' failed to start. Check logs with: journalctl -u $SERVICE_NAME -n 50"
    fi
fi

# ─── Done ─────────────────────────────────────────────────────────────────────
info "Setup complete."
echo ""
echo "  Service : $SERVICE_NAME"
echo "  Status  : $(systemctl is-active $SERVICE_NAME)"
echo "  Logs    : journalctl -u $SERVICE_NAME -f"
echo "  Deploy  : ./scripts/linux/deploy.sh"
echo ""
