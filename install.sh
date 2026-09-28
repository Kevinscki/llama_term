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
    echo "A new .env file has been created. Please edit it and fill in any secrets (OPENAI_URL_API, ANTHROPIC_URL_API, GEMINI_API)."
  else
    echo "No .env.example found – you will need to create a .env manually for API keys." >&2
  fi
else
  echo ".env already exists – leaving unchanged."
fi

# -------------------------------------------------------------------
# 5. Optional backend sanity check
# -------------------------------------------------------------------
echo "Default API_TYPE is openai_http (OpenAI-compatible /v1/chat/completions)."
if grep -qE "^API_TYPE=(openai_http|ollama_http)" .env 2>/dev/null; then
  echo "Ensure OPENAI_URL_ENDPOINT points at your gateway (e.g. Omniroute)."
  if grep -qiE "^OPENAI_API=(True|1|yes|on)" .env 2>/dev/null; then
    if ! grep -qE "^OPENAI_URL_API=.+" .env 2>/dev/null; then
      echo "OPENAI_API is enabled but OPENAI_URL_API looks empty in .env." >&2
    fi
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

If you use a bearer/API key, set OPENAI_URL_API (and/or ANTHROPIC_URL_API / GEMINI_API) in .env.

Enjoy!
EOF
