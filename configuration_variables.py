import os,re,secrets,tempfile
from dotenv import dotenv_values, load_dotenv
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

BASE_DIR = Path(__file__).resolve().parent
CURRENT_TOOL_NAME = "BASH_ROAST"
CURRENT_TOOL_NAME_FILE = CURRENT_TOOL_NAME+".md"
# Load local .env if present (never commit secrets)
load_dotenv(BASE_DIR / ".env", override=False)

def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


#stuff
# API_TYPE: openai_http | anthropic_http | gemini
API_TYPE = os.getenv("API_TYPE", "ollama_http")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
# Prefer environment / .env — never hardcode live keys in source
GEMINI_API = os.getenv("GEMINI_API", "") or os.getenv("GOOGLE_API_KEY", "")

# OpenAI-compatible (Ollama / Omniroute / LiteLLM / OpenAI, etc.)
OPENAI_MODEL = os.getenv("OPENAI_MODEL","gemma4:31b-cloud")
OPENAI_URL_ENDPOINT = (
    os.getenv("OPENAI_URL_ENDPOINT")
    or os.getenv("OPEAI_URL_ENDPOINT")  # common typo alias
    or os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/v1/chat/completions")
)
OPENAI_API = _env_bool("OPENAI_API", False)  # send Authorization when True
OPENAI_URL_API = os.getenv("OPENAI_URL_API")

# Anthropic Messages API (native or Anthropic-compatible proxy)
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
ANTHROPIC_URL_ENDPOINT = os.getenv(
    "ANTHROPIC_URL_ENDPOINT", "https://api.anthropic.com/v1/messages"
)
ANTHROPIC_API = _env_bool("ANTHROPIC_API", True)
ANTHROPIC_URL_API = os.getenv("ANTHROPIC_URL_API", "")
ANTHROPIC_VERSION = os.getenv("ANTHROPIC_VERSION", "2023-06-01")
ANTHROPIC_MAX_TOKENS = int(os.getenv("ANTHROPIC_MAX_TOKENS", "4096"))


HOMEDIR=Path(os.path.expanduser("~"))
USERNAME = os.getenv("USER") or os.getenv("USERNAME")
COMPUTERNAME = os.environ.get("COMPUTERNAME", os.uname().nodename if hasattr(os, "uname") else "PC")

log_file_type=False
another_type=False
HISTORY_DIR = BASE_DIR / "markdowns"
LOG_FILE = BASE_DIR / "logs" / "session.log"
SYSTEM_PROMPT=HISTORY_DIR / CURRENT_TOOL_NAME_FILE #default tool
USER_ERROR_TEMP = BASE_DIR / "user_errors_temp.txt"
TEMP_ERROR_LOG = BASE_DIR / "error_logs_temp.txt"

# Per-process runtime dir so concurrent sessions do not collide
RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="llama_term_"))
TEMP_SCRIPT = RUNTIME_DIR / "temp_script.sh"
PASTE_CMD_FILE = RUNTIME_DIR / "paste_cmd.sh"
# [t] capture: PTY transcript round-trips through this tmp file (write → read back)
CAPTURE_FILE = RUNTIME_DIR / "ai_output_buffer.txt"

# Per-session control markers (never use fixed public strings)
SESSION_ID = secrets.token_hex(8)
MARKER_EXIT = f"__LLAMA_EXIT_{SESSION_ID}__:"
MARKER_DIR = f"__LLAMA_DIR_{SESSION_ID}__:"
MARKER_END = f"__LLAMA_END_{SESSION_ID}__"
MARKER_AI_PWD = f"__LLAMA_AI_PWD_{SESSION_ID}__:"
MARKER_AI_END = f"__LLAMA_AI_END_{SESSION_ID}__"

# Back-compat alias (old code paths); prefer MARKER_END
SENTINEL = MARKER_END


LOG_LINE=1
HISTORY_LINES=0
HISTORY_TRAIL_LINES =0
MODEL_CONTEXT_LEN=7 #Model should have context

ENV1=HISTORY_DIR / ".shellrc"
ENV2=HOMEDIR / ".bashrc"
# Optional overlay from a local shellrc — not written on every output line
env={**os.environ, **dotenv_values(ENV1)} if ENV1.exists() else dict(os.environ)
current_dir=Path.cwd()
simulate_typing=True

# AI script approval — sticky auto-run never bypasses high-risk lines
ALWAYS_CONFIRM_RISKY = True
ALLOW_SESSION_AUTORUN = True  # 'a' enables non-risky auto-run for this session only

#risky bits (keyword scan — convenience, not a security boundary)
keywords=[
    "dd if", "usermod", "chmod", "chattr", "userdel", "exec",
    "rm -rf", "rmdir", "sudo", "umount", "systemctl", "iw", "rm ",
    "| bash", "|bash", "|sh", "| sh", "| /bin/bash", "|/bin/sh",
    "|/bin/bash", "| /bin/sh", "bash -c", "|zsh", "| zsh",
    "| /bin/zsh", "|/bin/zsh", "shred", "mkfs", "iptables",
    "ip6tables", "nft ", "crontab", "chmod -R", "chown -R",
    "curl |", "wget |", "> /dev/sd", "of=/dev/",
]


#Tracking (legacy unused paths kept for compatibility)
DIR_FILE="/tmp/__dir_llama__"
EXIT_CODE_FILE="/tmp/__exit_llama__"

BASE_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_DIR.mkdir(parents=True, exist_ok=True)
(LOG_FILE.parent).mkdir(parents=True, exist_ok=True)


#tools

CURRENT_TOOL_PATH = SYSTEM_PROMPT

TOOL_NAME_RE = re.compile(r'^\w+$')

EDITOR = os.environ.get("EDITOR", "vim")

TOOL_META_PROMPT = (
    "You write system prompts for a specialized command-line assistant tool. "
    "The user will give you a tool name and/or short description. "
    "Output ONLY the system prompt markdown for that tool — no preamble, no "
    "explanation, no code fences around the whole thing. "
    "You will include what  ```bash block format to be run "
    "The prompt must: (1) define the assistant's role narrowly around the "
    "named domain, (2) instruct it to explain syntax/commands clearly for "
    "learners, (3) instruct it to prefer safe, non-destructive examples, "
    "(4) NOT include instructions to bypass safety checks or execute "
    "(5) Include the command format if required inside the ```bash ``` block"
    "The commands will provide a system prompt framework and structure for an ai model using the prompt"
    "dangerous commands. End the file with the exact line EOTOOL on its own."
)

#embeds
EMBED_ROOT = HISTORY_DIR.resolve()

# Volume — INCLUDE default cap (FIX.md); None = unlimited if you override
MAX_INCLUDE_BYTES = int(os.getenv("MAX_INCLUDE_BYTES", "200000"))
MAX_FILE_BYTES = None
MAX_TREE_DEPTH = None

SENSITIVE_PATH_MARKERS = (
    ".ssh", ".gnupg", ".aws", ".azure", "id_rsa", "id_ed25519",
    ".env", "credentials", "shadow", "/etc/passwd", "kube/config",
    ".netrc", "token", "secret",
)

# Pasted / typed shell input larger than this is fed via a temp script so the
# persistent bash stdin PIPE (~64KiB) cannot fill and deadlock against stdout.
LARGE_STDIN_BYTES = 48_000

# Real-TTY trick — the persistent shell is PIPE-based (so state survives), but
# commands that need a true terminal are wrapped in script(1) at execution
# time: they get a fresh PTY *inside* the persistent bash, so colors,
# editors, pagers and REPLs work while cwd/env/functions still persist.
#   auto   = wrap only known TTY-hungry commands (default)
#   always = wrap every typed command (max fidelity, raw CRLF output)
#   off    = never wrap (legacy pipe behavior)
REALTTY_MODE = os.getenv("LLAMA_REALTTY", "auto").strip().lower()

TTY_COMMANDS = {
    # shells / multiplexers
    "bash", "sh", "zsh", "fish", "dash", "ksh", "csh", "tcsh", "nu",
    "screen", "tmux", "abduco", "dvtm",
    # editors
    "vim", "vi", "view", "vimdiff", "nvim", "nano", "micro", "helix", "hx",
    "emacs", "emacsclient", "pico", "joe", "ne",
    # pagers / docs
    "less", "more", "most", "man", "info", "pinfo",
    # monitors / system TUIs
    "watch", "top", "btop", "htop", "gtop", "atop", "iotop", "nmon",
    "powertop", "iftop", "nload", "bandwhich", "s-tui",
    # file managers
    "ncdu", "mc", "ranger", "lf", "yazi", "nnn", "vifm",
    # remote
    "ssh", "mosh", "telnet", "sftp", "ftp",
    # git/ops TUIs
    "fzf", "lazygit", "lazydocker", "tig", "gitui", "k9s",
    # REPLs
    "python", "python3", "ipython", "ipython3", "ptpython", "bpython",
    "node", "deno", "bun", "ruby", "irb", "pry", "julia", "lua", "php", "R",
    # databases (interactive clients)
    "psql", "mysql", "mariadb", "sqlite3", "mongosh", "mongo", "redis-cli",
    "clickhouse-client",
    # misc interactive
    "gpg", "pass", "crontab", "sudo", "su", "doas", "journalctl",
}

PTY_READ_BYTES = 65_536
AI_HTTP_TIMEOUT = (5, 300)  # connect, read
OLLAMA_TIMEOUT = AI_HTTP_TIMEOUT  # backward-compatible alias
AI_CAPTURE_MAX_CHARS = int(os.getenv("LLAMA_CAPTURE_CHARS", "24000"))

# AI context decision markers (toggle at runtime with FLAGS())
# repeat  = re-run embed scripts on every ASK()/error AI call
# embed   = attach LIVE HOST/TOOL CONTEXT to the model
# exitcode = include numeric exit status in failure prompts
REPEAT_EMBEDDING = True
INCLUDE_EMBEDDING = True
INCLUDE_EXIT_CODE = False

#what embeds can run
ALLOWED_EMBED_COMMANDS = {
    "neofetch":    [()],
    "cat":         [()],
    "uname":       [("-a",), ("-r",), ("-m",)],
    "ip":          [("addr",), ("-br", "addr"), ("route",)],
    "hostnamectl": [()],
    "uptime":      [()],
    "lscpu":       [()],
    "free":        [("-h",)],
    "nmap":        [("--help",), ("-h",)],
    "docker": [
        ("version",),
        ("info",),
        ("ps",),
        ("ps", "-a"),
        ("images",),
        ("network", "ls"),
        ("network", "inspect", "bridge"),
        (
            "ps",
            "--format",
            "{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}",
        ),
    ],
    "git":         [("--version",), ("status",), ("remote", "-v")],
    "python3":     [("--version"),("-v"),("-V")],
    "node":        [("--version"),("-V"),("-v")],
    "pwd":         [()],
    "whoami":      [()],
}

# Named multi-command snapshots for embed_json {"type":"script","name":"..."}
# Keep these read-only / inspect-only.
ALLOWED_EMBED_SCRIPTS = {
    "host_live": r"""
echo "=== host ==="
uname -a
hostnamectl 2>/dev/null | head -n 25 || true
echo "=== uptime ==="
uptime
echo "=== RAM (left / free) ==="
free -h
echo "=== host IPs ==="
ip -br addr 2>/dev/null || ip addr
echo "=== routes ==="
ip route 2>/dev/null || true
""",
    "docker_live": r"""
if ! command -v docker >/dev/null 2>&1; then
  echo "[-] docker binary not found"
  exit 0
fi
echo "=== docker version ==="
docker version 2>&1 || true
echo "=== docker info (brief) ==="
docker info 2>/dev/null | sed -n '1,40p' || true
echo "=== running containers ==="
docker ps --format 'table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' 2>&1 || true
echo "=== all containers ==="
docker ps -a --format 'table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' 2>&1 || true
echo "=== images ==="
docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}' 2>&1 || true
echo "=== networks ==="
docker network ls 2>&1 || true
echo "=== container IPs ==="
ids=$(docker ps -q 2>/dev/null || true)
if [ -z "$ids" ]; then
  echo "(no running containers)"
else
  for id in $ids; do
    docker inspect -f '{{.Name}} | ID={{.Id}} | IP={{range $k,$v := .NetworkSettings.Networks}}{{$k}}={{$v.IPAddress}} {{end}}| Ports={{json .NetworkSettings.Ports}}' "$id" 2>/dev/null || true
  done
fi
echo "=== bridge network ==="
docker network inspect bridge 2>/dev/null | head -n 80 || true
""",
}

#allowed paths to embed

ALLOWED_DIRS = [
    HISTORY_DIR.resolve(),
    (Path.home() / "temp" / "ideas").resolve(),
    (Path.home() /"Documents"/"Nodes").resolve()
]

REASON="high"
