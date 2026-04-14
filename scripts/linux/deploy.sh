#!/usr/bin/env bash
# =============================================================================
# deploy.sh — Update and restart the service on the VPS
#
# Usage:
#   chmod +x scripts/linux/deploy.sh
#   ./scripts/linux/deploy.sh
#
# What it does:
#   1. Pulls latest changes from GitHub
#   2. Compares requirements.txt hash with the saved one
#   3. Reinstalls dependencies only if they changed
#   4. Restarts the systemd service (always — gunicorn has no auto-reload)
#
# Requirements:
#   - setup.sh must have been run at least once
#   - SERVICE_NAME must match your actual .service file name
# =============================================================================

set -euo pipefail

# Always run from the project root (2 levels up from this script)
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

SERVICE_NAME="optimus-api"   # ← change to your actual .service name
GIT_BRANCH="master"            # ← change if your default branch is "master"
VENV_DIR=".venv"
REQUIREMENTS="requirements.txt"
HASH_FILE=".requirements.hash"

# ─── Output colors ───────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${GREEN}[optimus:deploy]${NC} $1"; }
warn()    { echo -e "${YELLOW}[optimus:deploy]${NC} $1"; }
error()   { echo -e "${RED}[optimus:deploy] $1${NC}"; exit 1; }

# ─── Ensure setup was run first ──────────────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    error "Virtualenv not found. Run first: ./scripts/linux/setup.sh"
fi

# ─── Pull latest changes from GitHub ─────────────────────────────────────────
info "Fetching changes from GitHub (branch: $GIT_BRANCH)..."
git fetch origin

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$GIT_BRANCH")

if [ "$LOCAL" = "$REMOTE" ]; then
    info "No new changes in the repository. Nothing to update."
    exit 0
fi

git pull origin "$GIT_BRANCH"
info "Code updated."

# ─── Activate virtualenv ─────────────────────────────────────────────────────
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# ─── Compare requirements.txt hash ───────────────────────────────────────────
CURRENT_HASH=$(sha256sum "$REQUIREMENTS")
PACKAGES_CHANGED=false

if [ ! -f "$HASH_FILE" ]; then
    warn "Hash file not found. Forcing dependency install."
    PACKAGES_CHANGED=true
elif [ "$CURRENT_HASH" != "$(cat "$HASH_FILE")" ]; then
    warn "requirements.txt changed. Updating dependencies..."
    PACKAGES_CHANGED=true
else
    info "requirements.txt unchanged. Skipping package install."
fi

# ─── Install packages only if they changed ───────────────────────────────────
if [ "$PACKAGES_CHANGED" = true ]; then
    info "Installing dependencies..."
    pip install --upgrade pip --quiet
    pip install -r "$REQUIREMENTS"

    # Update saved hash
    sha256sum "$REQUIREMENTS" > "$HASH_FILE"
    info "Dependencies updated and hash saved."
fi

# ─── Sync systemd service file if changed ────────────────────────────────────
SERVICE_SRC="optimus-api.service"
SERVICE_DEST="/etc/systemd/system/$SERVICE_NAME.service"

if [ -f "$SERVICE_SRC" ]; then
    if ! diff -q "$SERVICE_SRC" "$SERVICE_DEST" > /dev/null 2>&1; then
        info "Service file changed. Updating $SERVICE_DEST..."
        sudo cp "$SERVICE_SRC" "$SERVICE_DEST"
        sudo systemctl daemon-reload
        info "systemd daemon reloaded."
    else
        info "Service file unchanged. Skipping daemon-reload."
    fi
fi

# ─── Clean up temp_optimus on every deploy ───────────────────────────────────
# The service restart below calls purge_temp_root() at startup, but any files
# written after the last restart (orphaned chunks, assembled, compressed) won't
# be tracked in memory and won't be cleaned by cleanup_jobs_loop. We wipe the
# directory here, before the restart, so the disk is always clean after deploy.
TEMP_DIR="/home/opc/temp_optimus"
if [ -d "$TEMP_DIR" ]; then
    COUNT=$(find "$TEMP_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l)
    if [ "$COUNT" -gt 0 ]; then
        warn "Cleaning $COUNT orphan folder(s) from $TEMP_DIR..."
        rm -rf "${TEMP_DIR:?}/"*
        info "Temp directory cleaned."
    else
        info "Temp directory already empty."
    fi
fi

# ─── Restart service (always — gunicorn has no auto-reload) ──────────────────
info "Restarting service '$SERVICE_NAME'..."

if systemctl is-active --quiet "$SERVICE_NAME"; then
    sudo systemctl restart "$SERVICE_NAME"
else
    sudo systemctl start "$SERVICE_NAME"
fi

# Wait and verify
sleep 2

if systemctl is-active --quiet "$SERVICE_NAME"; then
    info "Service '$SERVICE_NAME' is running."
    systemctl status "$SERVICE_NAME" --no-pager -l
else
    error "Service '$SERVICE_NAME' failed to start. Check logs with: journalctl -u $SERVICE_NAME -n 50"
fi
