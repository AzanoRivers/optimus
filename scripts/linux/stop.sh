#!/usr/bin/env bash
# =============================================================================
# stop.sh — Stop the systemd service on the VPS
#
# Usage:
#   ./scripts/linux/stop.sh
#
# Requirements:
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

info()  { echo -e "${GREEN}[optimus:stop]${NC} $1"; }
warn()  { echo -e "${YELLOW}[optimus:stop]${NC} $1"; }
error() { echo -e "${RED}[optimus:stop] $1${NC}"; exit 1; }

# ─── Check current state ──────────────────────────────────────────────────────
if ! systemctl is-active --quiet "$SERVICE_NAME"; then
    warn "Service '$SERVICE_NAME' is not running."
    exit 0
fi

# ─── Stop ─────────────────────────────────────────────────────────────────────
info "Stopping service '$SERVICE_NAME'..."
sudo systemctl stop "$SERVICE_NAME"
sleep 1

if ! systemctl is-active --quiet "$SERVICE_NAME"; then
    info "Service '$SERVICE_NAME' stopped."
else
    error "Could not stop service '$SERVICE_NAME'. Check logs with: journalctl -u $SERVICE_NAME -n 50"
fi
