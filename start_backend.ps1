<#
PowerShell backend starter: creates .venv, installs deps, runs uvicorn
Run: .\start_backend.ps1
#>

param(
  [int]$Port = 8000
)

# Helper: find python
$python = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $python) {
  Write-Error "Python not found. Install Python 3.8+ and ensure 'python' is in PATH."
  exit 1
}
$python = $python.Path

# Create venv if missing
if (-not (Test-Path -Path ".venv")) {
  Write-Host "Creating virtualenv..."
  & $python -m venv .venv
}

# Activate venv
$activate = Join-Path -Path ".venv" -ChildPath "Scripts\Activate.ps1"
if (Test-Path $activate) {
  Write-Host "Activating .venv..."
  & $activate
} else {
  Write-Error "Activate script not found at $activate"
  exit 1
}

# Upgrade pip and install requirements
python -m pip install --upgrade pip
if (Test-Path "requirements.txt") {
  Write-Host "Installing requirements..."
  pip install -r requirements.txt
} else {
  Write-Host "No requirements.txt found; skipping installation."
}

# Check backend/.env
if (-not (Test-Path "backend\.env")) {
  Write-Warning "backend\.env not found. Add it if you need real API keys."
}

# Start uvicorn
Write-Host "Starting backend on http://127.0.0.1:$Port"
uvicorn backend.app:app --reload --port $Port