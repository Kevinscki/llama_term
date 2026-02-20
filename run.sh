#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
MODEL="qwen2.5-coder:3b"

echo "[*] AI Shell Setup Starting..."

# -------------------------
# Require sudo upfront
# -------------------------
if [ "$EUID" -ne 0 ]; then
    echo "[*] This script requires sudo privileges."
    echo "[*] Re-running with sudo..."
    exec sudo bash "$0" "$@"
fi

# -------------------------
# Install snap if missing
# -------------------------
if ! command -v snap &> /dev/null; then
    echo "[*] Installing snap..."
    apt update
    apt install snapd -y
fi

# -------------------------
# Enable snapd
# -------------------------
echo "[*] Enabling snapd..."
systemctl enable --now snapd

# -------------------------
# Install Ollama via snap
# -------------------------
if ! command -v ollama &> /dev/null; then
    echo "[*] Installing Ollama..."
    snap install ollama
else
    echo "[*] Ollama already installed."
fi

# -------------------------
# Pull model if missing
# -------------------------
if ! ollama list | grep -q "$MODEL"; then
    echo "[*] Pulling model: $MODEL"
    ollama pull "$MODEL"
else
    echo "[*] Model already available."
fi

# -------------------------
# Drop back to normal user
# -------------------------
REAL_USER="${SUDO_USER:-$USER}"
HOME_DIR=$(eval echo "~$REAL_USER")

echo "[*] Switching back to user: $REAL_USER"

sudo -u "$REAL_USER" bash <<EOF

cd "$PROJECT_DIR"

# Create virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "[*] Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

pip install --upgrade pip >/dev/null
pip install prompt_toolkit >/dev/null

echo "[*] Launching AI Shell..."
python3 main.py

EOF
