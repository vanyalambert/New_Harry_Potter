#!/usr/bin/env bash
set -euo pipefail

# Cross-Unix backend starter: creates .venv, installs deps, runs uvicorn
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Find python
PYTHON_CMD=""
for cmd in python3 python; do
  if command -v "$cmd" >/dev/null 2>&1; then
    PYTHON_CMD="$cmd"
    break
  fi
done

if [ -z "$PYTHON_CMD" ]; then
  echo "ERROR: Python not found. Install Python 3.8+ and try again."
  exit 1
fi

# Create venv if missing
if [ ! -d ".venv" ]; then
  echo "Creating virtualenv using $PYTHON_CMD..."
  "$PYTHON_CMD" -m venv .venv
fi

# Activate venv for this script
# shellcheck disable=SC1091
source .venv/bin/activate

# Upgrade pip & install requirements
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
  echo "Installing requirements..."
  pip install -r requirements.txt
else
  echo "No requirements.txt found; skipping pip install."
fi

# Ensure .env exists in backend/
if [ ! -f "backend/.env" ]; then
  echo "Warning: backend/.env not found. Create it before running in production. Using MOCK mode if GEMINI_API_KEY empty."
fi

# Run uvicorn
PORT="${PORT:-8000}"
echo "Starting backend on http://127.0.0.1:${PORT} (Ctrl-C to stop)"
# use reload in dev
uvicorn backend.app:app --reload --port "$PORT"