#!/usr/bin/env bash

# install.sh – set up the llama_term project
# -------------------------------------------------
# This script performs the steps a fresh user would need to get the
# project running locally. It is deliberately defensive: it checks for
# required tools, creates a virtual environment, installs Python
# dependencies, and prepares a .env file.
# -------------------------------------------------

# Exit on any error
set -e

# Determine the directory containing this script and cd there.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# -------------------------------------------------------------------
# 1. Verify that a suitable Python interpreter is available
# -------------------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 not found in PATH. Install Python 3.10+ first." >&2
  exit 1
fi
PYVER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if (( $(echo "$PYVER < 3.10" | bc -l) )); then
  echo "Error: Python $PYVER detected – version 3.10 or newer is required." >&2
  exit 1
fi

# -------------------------------------------------------------------
# 2. Create (or reuse) a virtual environment in .venv
# -------------------------------------------------------------------
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment in .venv..."
  python3 -m venv .venv
else
  echo "Virtual environment already exists – re‑using .venv"
fi

# Activate the environment for the remainder of this script
# shellcheck source=/dev/null
source ".venv/bin/activate"

# Upgrade pip for consistency
pip install --quiet --upgrade pip

# -------------------------------------------------------------------
# 3. Install Python package dependencies
# -------------------------------------------------------------------
if [ -f "requirements.txt" ]; then
  echo "Installing Python dependencies from requirements.txt..."
  pip install --quiet -r requirements.txt
else
  echo "Warning: requirements.txt not found – skipping pip install." >&2
fi

# -------------------------------------------------------------------
# 4. Prepare a .env file if the user hasn't provided one yet
# -------------------------------------------------------------------
if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "A new .env file has been created. Please edit it and fill in any secrets (e.g., GEMINI_API)."
  else
    echo "No .env.example found – you will need to create a .env manually if you use Gemini." >&2
  fi
else
  echo ".env already exists – leaving unchanged."
fi

# -------------------------------------------------------------------
# 5. Optional Ollama sanity check (only if you intend to use the local model)
# -------------------------------------------------------------------
if grep -q "^API_TYPE=ollama_http" .env 2>/dev/null; then
  if command -v ollama >/dev/null 2>&1; then
    echo "Ollama binary detected in PATH."
    # You could add a quick version check here if desired.
  else
    echo "Ollama not found in PATH. If you plan to use the Ollama backend, install it from https://ollama.ai/" >&2
  fi
fi

# -------------------------------------------------------------------
# 6. Final instructions for the user
# -------------------------------------------------------------------
cat <<'EOF'

Installation complete!

To start the interactive shell, run:

    source .venv/bin/activate   # activate the virtual environment (if not already active)
    python3 llama_shell.py

If you configured a Gemini API key, ensure the .env file contains a valid GEMINI_API value.

Enjoy!
EOF
