import os
from dotenv import dotenv_values
from pathlib import Path
ESC     = "\033[0m"
BLUE    = "\033[34m"
GREEN   = "\033[92m"
WHITE   = "\033[37m"
CYAN    = "\033[96m"
YELLOW  = "\033[33m"
RED     = "\033[31m"
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
GREY    = "\033[90m"

# Configuration
HOMEDIR=Path("/home/kelvin")
USERNAME = os.getenv("USER") or os.getenv("USERNAME")
OLLAMA_MODEL ="bash_model:latest"
COMPUTERNAME = os.environ.get("COMPUTERNAME", os.uname().nodename if hasattr(os, "uname") else "PC")
#BASE_DIR = Path.home() / "projects" / "ai" / "llama_term"
BASE_DIR = Path(__file__).resolve().parent
HISTORY_DIR = BASE_DIR / "markdowns"
LOG_FILE = HISTORY_DIR / "BASH.md"
USER_ERROR_TEMP = BASE_DIR / "user_errors_temp.txt"
TEMP_ERROR_LOG = BASE_DIR / "error_logs_temp.txt"
TEMP_SCRIPT = BASE_DIR / "temp_script.sh"
LOG_LINE=75
HISTORY_LINES=1  # history size n-lines (larger history not advised)
SENTINEL = "---CMD_END--"
ENV1=HISTORY_DIR / ".shellrc"
ENV2=HOMEDIR / ".bashrc"
env={**os.environ, **dotenv_values(ENV1)}
current_dir=Path.cwd()
simulate_typing=True
keywords=["rm -rf", "rmdir", "sudo", "umount","systemctl","iw"]  # Dangerous keywords list

# Ensure directories exist
BASE_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_DIR.mkdir(parents=True, exist_ok=True)
