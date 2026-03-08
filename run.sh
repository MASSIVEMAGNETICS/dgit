#!/usr/bin/env bash
# =============================================================================
# VICTOR COMMAND CENTER — STARTUP SCRIPT
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="$SCRIPT_DIR/.venv"

# Create virtualenv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
  echo "[victor] Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

# Activate virtualenv
source "$VENV_DIR/bin/activate"

# Install / upgrade requirements
echo "[victor] Installing requirements..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# Ensure storage dirs exist
mkdir -p storage/artifacts storage/vector_index

# Start the server
echo "[victor] Starting Victor Command Center on http://0.0.0.0:8000 ..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
