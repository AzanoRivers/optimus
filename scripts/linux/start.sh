#!/usr/bin/env bash
# =============================================================================
# start.sh — Start the systemd service on the VPS
#
# Usage:
#   ./scripts/linux/start.sh
#
# Requirements:
#   - setup.sh must have been run at least once
#   - SERVICE_NAME must match your actual .service file name
# =============================================================================

set -euo pipefail

# Always run from the project root (2 levels up from this script)
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

SERVICE_NAME="optimus-api"   # ← change to your actual .service name

# ─── Output colors ────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[optimus:start]${NC} $1"; }
warn()  { echo -e "${YELLOW}[optimus:start]${NC} $1"; }
error() { echo -e "${RED}[optimus:start] $1${NC}"; exit 1; }

# ─── Check current state ──────────────────────────────────────────────────────
if systemctl is-active --quiet "$SERVICE_NAME"; then
    warn "Service '$SERVICE_NAME' is already running."
    systemctl status "$SERVICE_NAME" --no-pager -l
    exit 0
fi

# ─── Start ────────────────────────────────────────────────────────────────────
info "Starting service '$SERVICE_NAME'..."
sudo systemctl start "$SERVICE_NAME"
sleep 2

if systemctl is-active --quiet "$SERVICE_NAME"; then
    info "Service '$SERVICE_NAME' is running."
    systemctl status "$SERVICE_NAME" --no-pager -l
else
    error "Service '$SERVICE_NAME' failed to start. Check logs with: journalctl -u $SERVICE_NAME -n 50"
fi
