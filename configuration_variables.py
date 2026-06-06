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
API_TYPE="ollama_http"
GEMINI_MODEL="gemini-2.5-flash"
GEMINI_API="AIzaSyDRkcih2PvNykPcKqMBRawzG0VfaZwpGeE"
OLLAMA_MODEL ="qwen2.5-coder:7b"




HOMEDIR=Path("/home/kelvin")
USERNAME = os.getenv("USER") or os.getenv("USERNAME")
COMPUTERNAME = os.environ.get("COMPUTERNAME", os.uname().nodename if hasattr(os, "uname") else "PC")
#BASE_DIR = Path.home() / "projects" / "ai" / "llama_term"

log_file_type=False
another_type=False
BASE_DIR = Path(__file__).resolve().parent
HISTORY_DIR = BASE_DIR / "markdowns"
LOG_FILE = HISTORY_DIR / "BASH_LEGACY.md"
SYSTEM_PROMPT=HISTORY_DIR / "BASH.md" #Non Legacy
USER_ERROR_TEMP = BASE_DIR / "user_errors_temp.txt"
TEMP_ERROR_LOG = BASE_DIR / "error_logs_temp.txt"
TEMP_SCRIPT = BASE_DIR / "temp_script.sh"


LOG_LINE=1
HISTORY_LINES=0     # history size n-lines (larger history not advised)
HISTORY_TRAIL_LINES =0 #Continous history to keep
MODEL_CONTEXT_LEN=7 #Non Legacy


SENTINEL = "---CMD_END--"
ENV1=HISTORY_DIR / ".shellrc"
ENV2=HOMEDIR / ".bashrc"
env={**os.environ, **dotenv_values(ENV1)}
current_dir=Path.cwd()
simulate_typing=True
keywords=["rm -rf", "rmdir", "sudo", "umount","systemctl","iw", "rm", "| bash", "|bash", "|sh", "| sh","| /bin/bash","|/bin/sh","|/bin/bash","| /bin/sh","bash -c","|zsh","| zsh","| /bin/zsh","|/bin/zsh", "shred","export"]  # Dangerous keywords list




# Ensure directories exist
BASE_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_DIR.mkdir(parents=True, exist_ok=True)
