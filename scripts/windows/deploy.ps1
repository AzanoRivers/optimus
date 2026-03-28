# =============================================================================
# deploy.ps1 — Pull changes and update dependencies (Windows / PowerShell)
#
# Usage:
#   .\scripts\windows\deploy.ps1
#
# What it does:
#   1. Pulls latest changes from GitHub
#   2. Compares requirements.txt hash with the saved one
#   3. Reinstalls dependencies only if they changed
#
# Note: uvicorn runs in foreground via start.ps1 with --reload.
#       Code-only changes are picked up automatically.
#       If packages changed, stop uvicorn (Ctrl+C) and run start.ps1 again.
#
# For real VPS deployment use scripts/linux/deploy.sh via SSH.
# =============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Always run from the project root (2 levels up from this script)
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..") 
Set-Location $ProjectRoot

$VenvDir      = ".venv"
$Requirements = "requirements.txt"
$HashFile     = ".requirements.hash"
$GitBranch    = "master"   # ← change if your default branch is "master"

function Write-Info  { param($msg) Write-Host "[optimus:deploy]" -ForegroundColor Green -NoNewline; Write-Host " $msg" -ForegroundColor White }
function Write-Warn  { param($msg) Write-Host "[optimus:deploy]" -ForegroundColor Yellow -NoNewline; Write-Host " $msg" -ForegroundColor White }
function Write-Err   { param($msg) Write-Host "[optimus:deploy] $msg" -ForegroundColor Red; exit 1 }

# ─── Ensure setup was run first ──────────────────────────────────────────────
if (-not (Test-Path $VenvDir)) {
    Write-Err "Virtualenv not found. Run first: .\scripts\windows\setup.ps1"
}

# ─── Pull latest changes from GitHub ─────────────────────────────────────────
Write-Info "Fetching changes from GitHub (branch: $GitBranch)..."
git fetch origin

$local  = git rev-parse HEAD
$remote = git rev-parse "origin/$GitBranch"

if ($local -eq $remote) {
    Write-Info "No new changes in the repository. Nothing to update."
    exit 0
}

git pull origin $GitBranch
Write-Info "Code updated."

# ─── Activate virtualenv ─────────────────────────────────────────────────────
$activateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
& $activateScript

# ─── Compare requirements.txt hash ───────────────────────────────────────────
$currentHash = (Get-FileHash $Requirements -Algorithm SHA256).Hash
$packagesChanged = $false

if (-not (Test-Path $HashFile)) {
    Write-Warn "Hash file not found. Forcing dependency install."
    $packagesChanged = $true
} elseif ($currentHash -ne (Get-Content $HashFile -Raw).Trim()) {
    Write-Warn "requirements.txt changed. Updating dependencies..."
    $packagesChanged = $true
} else {
    Write-Info "requirements.txt unchanged. Skipping package install."
}

# ─── Install packages only if they changed ───────────────────────────────────
if ($packagesChanged) {
    Write-Info "Installing dependencies..."
    python -m pip install --upgrade pip --quiet
    pip install -r $Requirements

    $currentHash | Set-Content $HashFile
    Write-Info "Dependencies updated and hash saved."

    Write-Host ""
    Write-Warn "Packages changed — stop uvicorn (Ctrl+C) and run start.ps1 again."
    Write-Host ""
} else {
    Write-Info "Code-only changes — uvicorn (--reload) reloaded automatically."
}

    Write-Host ""
} else {
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    Write-Err "uvicorn failed to start. Run it manually to see errors: uvicorn app.main:app --reload"
}
