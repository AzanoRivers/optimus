# =============================================================================
# setup.ps1 — One-time environment setup (Windows / PowerShell)
#
# Usage:
#   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned  # only the first time
#   .\scripts\windows\setup.ps1
#
# Requirements:
#   - Python 3.9+ installed and available as "python", "python3" or "python3.x"
#   - Run from the project root
# =============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Always run from the project root (2 levels up from this script)
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..") 
Set-Location $ProjectRoot

$VenvDir     = ".venv"
$Requirements = "requirements.txt"
$HashFile    = ".requirements.hash"
$EnvFile     = ".env"
$EnvExample  = ".env.example"

function Write-Info  { param($msg) Write-Host "[optimus:setup]" -ForegroundColor Green -NoNewline; Write-Host " $msg" -ForegroundColor White }
function Write-Warn  { param($msg) Write-Host "[optimus:setup]" -ForegroundColor Yellow -NoNewline; Write-Host " $msg" -ForegroundColor White }
function Write-Err   { param($msg) Write-Host "[optimus:setup] $msg" -ForegroundColor Red; exit 1 }

# ─── Check Python 3.9+ ────────────────────────────────────────────────────────
Write-Info "Checking Python 3.9+..."

$pythonCmd = $null
foreach ($cmd in @("python3.9", "python3", "python")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $version = & $cmd --version 2>&1
        if ($version -match "Python 3\.([9]|[1-9]\d+)") {
            $pythonCmd = $cmd
            break
        }
    }
}

if (-not $pythonCmd) {
    Write-Err "Python 3.9+ not found. Download it at https://www.python.org/downloads/"
}
Write-Info "Using: $pythonCmd ($( & $pythonCmd --version))"

# ─── Create virtualenv ───────────────────────────────────────────────────────
if (Test-Path $VenvDir) {
    Write-Warn "Virtualenv '$VenvDir' already exists. Skipping creation."
} else {
    Write-Info "Creating virtualenv in $VenvDir..."
    & $pythonCmd -m venv $VenvDir
    Write-Info "Virtualenv created."
}

# ─── Activate virtualenv ─────────────────────────────────────────────────────
$activateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    Write-Err "Activation script not found: $activateScript"
}
& $activateScript

# ─── Install / update dependencies ───────────────────────────────────────────
Write-Info "Upgrading pip..."
python -m pip install --upgrade pip --quiet

Write-Info "Installing dependencies from $Requirements..."
pip install -r $Requirements

# Save hash so deploy.ps1 can detect changes later
$hash = (Get-FileHash $Requirements -Algorithm SHA256).Hash
$hash | Set-Content $HashFile
Write-Info "Requirements hash saved to $HashFile"

# ─── Configure .env ──────────────────────────────────────────────────────────
if (-not (Test-Path $EnvFile)) {
    if (Test-Path $EnvExample) {
        Copy-Item $EnvExample $EnvFile
        Write-Warn ".env created from .env.example — review and update the variables."
    } else {
        Write-Warn "$EnvExample not found. Create the .env file manually."
    }
} else {
    Write-Info ".env already exists. Not overwritten."
}

# ─── Done ─────────────────────────────────────────────────────────────────────
Write-Info "Setup complete. Next steps:"
Write-Host ""
Write-Host "  1. Edit .env with your real values"
Write-Host "  2. Start the local server with:"
Write-Host "     .venv\Scripts\uvicorn.exe app.main:app --reload"
Write-Host "  3. For future updates run: .\scripts\windows\deploy.ps1"
Write-Host ""
