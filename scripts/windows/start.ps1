# =============================================================================
# start.ps1 — Start uvicorn in foreground with auto-reload (Windows / PowerShell)
#
# Usage:
#   .\scripts\windows\start.ps1
#
# Press Ctrl+C to stop.
#
# Requirements:
#   - setup.ps1 must have been run at least once
# =============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Always run from the project root (2 levels up from this script)
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..") 
Set-Location $ProjectRoot

$VenvDir = ".venv"
$Host_   = "127.0.0.1"
$Port    = 8000

function Write-Info { param($msg) Write-Host "[optimus:start]" -ForegroundColor Green -NoNewline; Write-Host " $msg" -ForegroundColor White }
function Write-Err  { param($msg) Write-Host "[optimus:start] $msg" -ForegroundColor Red; exit 1 }

# ─── Ensure setup was run first ───────────────────────────────────────────────
if (-not (Test-Path $VenvDir)) {
    Write-Err "Virtualenv not found. Run first: .\scripts\windows\setup.ps1"
}

# ─── Start uvicorn in foreground ──────────────────────────────────────────────
Write-Info "Starting uvicorn at http://${Host_}:${Port} (auto-reload enabled) ..."
Write-Info "Press Ctrl+C to stop."
Write-Host ""

& "$VenvDir\Scripts\uvicorn.exe" app.main:app --host $Host_ --port $Port --reload
