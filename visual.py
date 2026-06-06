"""
llama_term — Visual & UI layer
Drop-in replacement for all print/banner/help/prompt styling.
Requires: no new deps beyond what the project already uses.
"""

import os
import sys
import time
import shutil
import random

# ══════════════════════════════════════════════════════════════════════════════
#  PALETTE  –  deep-space neon noir
# ══════════════════════════════════════════════════════════════════════════════
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
ITALIC  = "\033[3m"
UNDER   = "\033[4m"
BLINK   = "\033[5m"

# Foreground
BLACK   = "\033[30m"
RED     = "\033[38;5;196m"
ORANGE  = "\033[38;5;208m"
YELLOW  = "\033[38;5;220m"
GREEN   = "\033[38;5;46m"
TEAL    = "\033[38;5;51m"
CYAN    = "\033[38;5;87m"
BLUE    = "\033[38;5;27m"
PURPLE  = "\033[38;5;135m"
PINK    = "\033[38;5;213m"
WHITE   = "\033[97m"
GREY    = "\033[38;5;244m"
LGREY   = "\033[38;5;250m"
DGREY   = "\033[38;5;238m"

# Background
BG_BLACK  = "\033[40m"
BG_DGREY  = "\033[48;5;234m"
BG_RED    = "\033[48;5;196m"
BG_CYAN   = "\033[48;5;87m"
BG_YELLOW = "\033[48;5;220m"

# Composed shortcuts
ERR   = f"{BOLD}{RED}"
WARN  = f"{BOLD}{YELLOW}"
INFO  = f"{BOLD}{CYAN}"
OK    = f"{BOLD}{GREEN}"
SUB   = f"{DIM}{GREY}"
LOGO  = f"{BOLD}{CYAN}"
ACCENT= f"{BOLD}{PINK}"

# ══════════════════════════════════════════════════════════════════════════════
#  TERMINAL GEOMETRY
# ══════════════════════════════════════════════════════════════════════════════
def _tw() -> int:
    return shutil.get_terminal_size((100, 40)).columns

def _center(text: str, raw_len: int | None = None, width: int | None = None) -> str:
    """Center `text` (which may contain ANSI escapes) inside `width` columns."""
    w = width or _tw()
    # strip ANSI for length calc
    import re
    visible = re.sub(r'\033\[[0-9;]*m', '', text)
    pad = max(0, (w - len(visible)) // 2)
    return " " * pad + text

def _hline(char="─", color=DGREY, width: int | None = None) -> str:
    w = width or _tw()
    return f"{color}{char * w}{RESET}"

def _box_line(inner: str, visible_len: int, width: int | None = None,
              left="│", right="│", lc=DGREY, rc=DGREY) -> str:
    w = (width or _tw()) - 2          # minus two border chars
    pad = max(0, w - visible_len)
    return f"{lc}{left}{RESET}{inner}{' ' * pad}{rc}{right}{RESET}"

# ══════════════════════════════════════════════════════════════════════════════
#  GLITCH TEXT  –  random zalgo-style corruption pass
# ══════════════════════════════════════════════════════════════════════════════
_GLITCH_CHARS = "▓▒░▄▀■□▪▫◆◇○●◌"

def glitch(text: str, intensity: float = 0.18) -> str:
    out = []
    for ch in text:
        if ch != " " and random.random() < intensity:
            out.append(random.choice(_GLITCH_CHARS))
        else:
            out.append(ch)
    return "".join(out)

# ══════════════════════════════════════════════════════════════════════════════
#  SCANLINE ANIMATION  –  prints lines top-down with a tiny delay
# ══════════════════════════════════════════════════════════════════════════════
def scanline_print(lines: list[str], delay: float = 0.018) -> None:
    for line in lines:
        print(line)
        time.sleep(delay)

# ══════════════════════════════════════════════════════════════════════════════
#  LOGO  –  hand-crafted block-letter ASCII, 7 rows tall
# ══════════════════════════════════════════════════════════════════════════════
_LOGO_LINES = [
    r" ██╗     ██╗      █████╗ ███╗   ███╗ █████╗     ████████╗███████╗██████╗ ███╗   ███╗",
    r" ██║     ██║     ██╔══██╗████╗ ████║██╔══██╗    ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║",
    r" ██║     ██║     ███████║██╔████╔██║███████║       ██║   █████╗  ██████╔╝██╔████╔██║",
    r" ██║     ██║     ██╔══██║██║╚██╔╝██║██╔══██║       ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║",
    r" ███████╗███████╗██║  ██║██║ ╚═╝ ██║██║  ██║       ██║   ███████╗██║  ██║██║ ╚═╝ ██║",
    r" ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝       ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝",
]

# Color gradient across logo lines: cyan → teal → cyan
_LOGO_COLORS = [
    f"{BOLD}\033[38;5;51m",
    f"{BOLD}\033[38;5;45m",
    f"{BOLD}\033[38;5;87m",
    f"{BOLD}\033[38;5;51m",
    f"{BOLD}\033[38;5;45m",
    f"{BOLD}\033[38;5;39m",
]

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN BANNER
# ══════════════════════════════════════════════════════════════════════════════
def show_header() -> None:
    tw = _tw()
    lines = []

    # ── top void ──────────────────────────────────────────────────────────────
    lines.append("")

    # ── outer frame top ───────────────────────────────────────────────────────
    lines.append(f"{DGREY}╔{'═' * (tw - 2)}╗{RESET}")
    lines.append(f"{DGREY}║{' ' * (tw - 2)}║{RESET}")

    # ── logo (scaled / centered) ──────────────────────────────────────────────
    for i, row in enumerate(_LOGO_LINES):
        col = _LOGO_COLORS[i % len(_LOGO_COLORS)]
        visible_len = len(row)
        pad = max(0, (tw - 2 - visible_len) // 2)
        inner = f"{' ' * pad}{col}{row}{RESET}{' ' * pad}"
        lines.append(f"{DGREY}║{RESET}{inner}{DGREY}║{RESET}")

    lines.append(f"{DGREY}║{' ' * (tw - 2)}║{RESET}")

    # ── tagline ───────────────────────────────────────────────────────────────
    tagline = f"{DIM}{LGREY}// neural-powered interactive shell  ·  v0.3-beta  ·  by {RESET}{CYAN}Kevinscki{RESET}"
    import re
    tl_vis = len(re.sub(r'\033\[[0-9;]*m', '', tagline))
    tl_pad = max(0, (tw - 2 - tl_vis) // 2)
    lines.append(f"{DGREY}║{RESET}{' ' * tl_pad}{tagline}{' ' * tl_pad}{DGREY}║{RESET}")
    lines.append(f"{DGREY}║{' ' * (tw - 2)}║{RESET}")

    # ── separator ─────────────────────────────────────────────────────────────
    lines.append(f"{DGREY}╠{'═' * (tw - 2)}╣{RESET}")

    # ── status bar ────────────────────────────────────────────────────────────
    ollama_ok = bool(shutil.which("ollama"))
    s_ai  = f"{OK}◉ AI READY{RESET}"   if ollama_ok else f"{ERR}◎ AI OFFLINE{RESET}"
    s_sh  = f"{OK}◉ SHELL ACTIVE{RESET}"
    s_mod = f"{WARN}◈ BETA BUILD{RESET}"
    status_inner = f"  {s_ai}   {DGREY}│{RESET}   {s_sh}   {DGREY}│{RESET}   {s_mod}  "
    import re
    st_vis = len(re.sub(r'\033\[[0-9;]*m', '', status_inner))
    lines.append(f"{DGREY}║{RESET}{status_inner}{' ' * max(0, tw - 2 - st_vis)}{DGREY}║{RESET}")
    lines.append(f"{DGREY}╠{'═' * (tw - 2)}╣{RESET}")
    lines.append(f"{DGREY}║{' ' * (tw - 2)}║{RESET}")

    # ── command quick-ref (two-column) ────────────────────────────────────────
    cmds = [
        ("LOAD()",    "warm up the AI model context"),
        ("BUMP()",    "flush + reset model session"),
        ("BANNER()",  "redisplay this banner"),
        ("RESET()",   "restart the shell process"),
        ("CHAT()",    "drop into raw ollama chat"),
        ("INCLUDE() <file>", "attach a file to AI context"),
        ("help",      "full command reference"),
        ("exit / quit", "terminate the shell"),
    ]
    col_w = (tw - 6) // 2
    for i in range(0, len(cmds), 2):
        left_cmd, left_desc = cmds[i]
        lstr = f"  {BOLD}{CYAN}{left_cmd:<18}{RESET}{DIM}{LGREY}{left_desc}{RESET}"
        lvis = 2 + len(left_cmd) + 2 + len(left_desc) + 2

        if i + 1 < len(cmds):
            right_cmd, right_desc = cmds[i + 1]
            rstr = f"  {BOLD}{CYAN}{right_cmd:<18}{RESET}{DIM}{LGREY}{right_desc}{RESET}"
            rvis = 2 + len(right_cmd) + 2 + len(right_desc)
        else:
            rstr, rvis = "", 0

        inner = f"{lstr}{' ' * max(0, col_w - lvis)}{DGREY}┊{RESET}{rstr}"
        ivislen = lvis + max(0, col_w - lvis) + 1 + rvis
        lines.append(f"{DGREY}║{RESET}{inner}{' ' * max(0, tw - 2 - ivislen)}{DGREY}║{RESET}")

    lines.append(f"{DGREY}║{' ' * (tw - 2)}║{RESET}")

    # ── hotkey bar ────────────────────────────────────────────────────────────
    hotkeys = (
        f"  {DGREY}[{RESET}{YELLOW}TAB{RESET}{DGREY}]{RESET}{DIM}{GREY} complete  {RESET}"
        f"{DGREY}[{RESET}{YELLOW}Ctrl+C{RESET}{DGREY}]{RESET}{DIM}{GREY} interrupt  {RESET}"
        f"{DGREY}[{RESET}{YELLOW}Ctrl+D{RESET}{DGREY}]{RESET}{DIM}{GREY} EOF / exit chat  {RESET}"
        f"{DGREY}[{RESET}{YELLOW}↑↓{RESET}{DGREY}]{RESET}{DIM}{GREY} history  {RESET}"
    )
    import re
    hk_vis = len(re.sub(r'\033\[[0-9;]*m', '', hotkeys))
    lines.append(f"{DGREY}║{RESET}{hotkeys}{' ' * max(0, tw - 2 - hk_vis)}{DGREY}║{RESET}")
    lines.append(f"{DGREY}║{' ' * (tw - 2)}║{RESET}")
    lines.append(f"{DGREY}╚{'═' * (tw - 2)}╝{RESET}")
    lines.append("")

    # ── repo line ─────────────────────────────────────────────────────────────
    repo = f"{DIM}  ↗  {RESET}{UNDER}{TEAL}https://github.com/Kevinscki/llama_term{RESET}"
    lines.append(repo)
    lines.append("")

    scanline_print(lines, delay=0.008)


# ══════════════════════════════════════════════════════════════════════════════
#  HELP  –  full reference, grouped + styled
# ══════════════════════════════════════════════════════════════════════════════
def show_help() -> None:
    tw = _tw()
    W = tw - 4

    def section(title: str) -> None:
        bar = f"{DGREY}├{'─' * (W + 2)}┤{RESET}"
        lbl = f" {BOLD}{PINK}{title}{RESET} "
        import re
        lbl_vis = 1 + len(title) + 1
        print(f"{DGREY}│{RESET} {BOLD}{PINK}{title}{RESET}{' ' * max(0, W - lbl_vis + 1)}{DGREY}│{RESET}")
        print(bar)

    def row(key: str, val: str, key_w: int = 22) -> None:
        k = f"  {BOLD}{CYAN}{key}{RESET}"
        v = f"{DIM}{LGREY}{val}{RESET}"
        import re
        k_vis = 2 + len(key)
        v_vis = len(val)
        gap = max(1, key_w - len(key))
        inner = f"{k}{' ' * gap}{v}"
        inner_vis = k_vis + gap + v_vis
        print(f"{DGREY}│{RESET}{inner}{' ' * max(0, W + 2 - inner_vis)}{DGREY}│{RESET}")

    def blank() -> None:
        print(f"{DGREY}│{' ' * (W + 2)}│{RESET}")

    print()
    print(f"{DGREY}╭{'─' * (W + 2)}╮{RESET}")
    blank()
    title_str = f"  {BOLD}{WHITE}llama_term  {RESET}{DIM}{GREY}·  command reference{RESET}"
    import re
    t_vis = len(re.sub(r'\033\[[0-9;]*m', '', title_str))
    print(f"{DGREY}│{RESET}{title_str}{' ' * max(0, W + 2 - t_vis)}{DGREY}│{RESET}")
    blank()
    print(f"{DGREY}├{'─' * (W + 2)}┤{RESET}")

    # ── Shell builtins ────────────────────────────────────────────────────────
    blank()
    section("SHELL BUILTINS")
    blank()
    row("exit / quit",   "terminate the shell session")
    row("clear / cls",   "wipe the screen")
    row("help",          "display this reference")
    blank()

    # ── AI controls ───────────────────────────────────────────────────────────
    section("AI CONTROLS")
    blank()
    row("LOAD()",        "feed log file into model — warms context")
    row("BUMP()",        "spawn a reset ping — clears hallucinations")
    row("CHAT()",        "interactive raw ollama session  (Ctrl+D exits)")
    row("INCLUDE() <f>", "read file, attach contents to next AI prompt")
    blank()

    # ── Shell controls ────────────────────────────────────────────────────────
    section("SHELL CONTROLS")
    blank()
    row("RESET()",       "restart the bash subprocess (env preserved)")
    row("BANNER()",      "redisplay the startup banner")
    blank()

    # ── Behaviour notes ───────────────────────────────────────────────────────
    section("BEHAVIOUR")
    blank()
    row("auto-fix",      "on non-zero exit → AI analyses + suggests a patch")
    row("always-exec",   "answer 'a' at the fix prompt to auto-run all fixes")
    row("multiline",     "incomplete syntax → shell drops to  >  continuation")
    row("tab-complete",  "paths + common commands via prompt_toolkit")
    blank()

    # ── Risk words ────────────────────────────────────────────────────────────
    section("RISK DETECTION")
    blank()
    warn_line = f"  {DIM}{LGREY}Dangerous keywords in AI output are highlighted in {RESET}{ERR}RED{RESET}{DIM}{LGREY} and auto-exec is blocked.{RESET}"
    import re
    wl_vis = len(re.sub(r'\033\[[0-9;]*m', '', warn_line))
    print(f"{DGREY}│{RESET}{warn_line}{' ' * max(0, W + 2 - wl_vis)}{DGREY}│{RESET}")
    blank()

    # ── Logging ───────────────────────────────────────────────────────────────
    section("LOGGING")
    blank()
    row("log scope",     "only failed commands + AI responses are stored")
    row("rotation",      "log auto-trims to keep size bounded")
    row("temp files",    "cleaned up after each AI interaction")
    blank()

    # ── Deps ──────────────────────────────────────────────────────────────────
    section("REQUIREMENTS")
    blank()
    row("ollama",        "https://ollama.ai/  — inference backend")
    row("model",         "ollama pull qwen2.5-coder:3b  (or configured model)")
    row("prompt_toolkit","pip install prompt_toolkit")
    blank()

    print(f"{DGREY}╰{'─' * (W + 2)}╯{RESET}")
    print()


# ══════════════════════════════════════════════════════════════════════════════
#  PROMPT STRING builder
# ══════════════════════════════════════════════════════════════════════════════
def build_prompt(username: str, hostname: str, cwd: str) -> str:
    """
    Returns an ANSI prompt string for use with ANSI() from prompt_toolkit.

    Layout:
      ╭─[user@host]──[~/some/path]──[git:main*]
      ╰─▶ $
    """
    # shorten very long paths
    home = os.path.expanduser("~")
    display_cwd = cwd.replace(home, "~") if cwd.startswith(home) else cwd
    if len(display_cwd) > 40:
        parts = display_cwd.split(os.sep)
        display_cwd = os.sep.join(["…"] + parts[-2:])

    # optional: git branch
    git_seg = ""
    try:
        import subprocess as _sp
        branch = _sp.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=_sp.DEVNULL, text=True, cwd=cwd
        ).strip()
        dirty = bool(_sp.check_output(
            ["git", "status", "--porcelain"],
            stderr=_sp.DEVNULL, text=True, cwd=cwd
        ).strip())
        marker = f"{YELLOW}✦{RESET}" if dirty else f"{GREEN}✔{RESET}"
        git_seg = f"{DGREY}──{RESET}{DGREY}[{RESET}{PURPLE}{branch}{RESET}{marker}{DGREY}]{RESET}"
    except Exception:
        pass

    user_col = CYAN if username != "root" else RED
    top = (
        f"{DGREY}╭─{RESET}"
        f"{DGREY}[{RESET}{user_col}{BOLD}{username}{RESET}"
        f"{DGREY}@{RESET}{WHITE}{BOLD}{hostname}{RESET}{DGREY}]{RESET}"
        f"{DGREY}──{RESET}"
        f"{DGREY}[{RESET}{TEAL}{display_cwd}{RESET}{DGREY}]{RESET}"
        f"{git_seg}"
    )
    bottom = f"{DGREY}╰─▶{RESET}{YELLOW}{BOLD} $ {RESET}"
    return f"{top}\n{bottom}"


def build_include_prompt(username: str, hostname: str, cwd: str, filename: str) -> str:
    home = os.path.expanduser("~")
    display_cwd = cwd.replace(home, "~") if cwd.startswith(home) else cwd
    top = (
        f"{DGREY}╭─{RESET}"
        f"{DGREY}[{RESET}{CYAN}{BOLD}{username}{RESET}"
        f"{DGREY}@{RESET}{WHITE}{BOLD}{hostname}{RESET}{DGREY}]{RESET}"
        f"{DGREY}──{RESET}{DGREY}[{RESET}{TEAL}{display_cwd}{RESET}{DGREY}]{RESET}"
        f"{DGREY}──{RESET}{DGREY}[{RESET}{ORANGE}📁 {WHITE}{filename}{RESET}{DGREY}]{RESET}"
    )
    bottom = f"{DGREY}╰─▶{RESET}{ORANGE}{BOLD} $ {RESET}"
    return f"{top}\n{bottom}"


# ══════════════════════════════════════════════════════════════════════════════
#  STATUS / FEEDBACK  messages
# ══════════════════════════════════════════════════════════════════════════════
def msg_processing() -> None:
    tw = _tw()
    bar = f"{DIM}{DGREY}{'─' * tw}{RESET}"
    print(bar)
    print(f"  {BLINK}{CYAN}◌{RESET}  {BOLD}{WHITE}processing{RESET}  {DIM}{GREY}— querying neural backend…{RESET}")
    print(bar)

def msg_suggestion_header(elapsed: float, risk_count: int) -> None:
    tw = _tw()
    elapsed_str = f"{elapsed:.3f}s"
    if risk_count:
        badge = f"{BG_RED}{BOLD} ⚠  {risk_count} RISK{'S' if risk_count > 1 else ''} DETECTED {RESET}"
        label = f"  {CYAN}◆{RESET}  {WHITE}suggestion ready{RESET}  {DIM}{GREY}({elapsed_str}){RESET}  {badge}"
    else:
        badge = f"\033[48;5;22m{BOLD}{GREEN} ✔  CLEAN {RESET}"
        label = f"  {CYAN}◆{RESET}  {WHITE}suggestion ready{RESET}  {DIM}{GREY}({elapsed_str}){RESET}  {badge}"
    print()
    print(label)
    print()

def msg_divider() -> None:
    tw = _tw()
    print(f"{DIM}{DGREY}{'╌' * tw}{RESET}")

def msg_executing() -> None:
    print(f"\n  {OK}▶{RESET}  {BOLD}{WHITE}executing suggestion…{RESET}\n")

def msg_skipped() -> None:
    print(f"\n  {WARN}◎{RESET}  {DIM}{YELLOW}suggestion skipped{RESET}\n")

def msg_error(text: str) -> None:
    tw = _tw()
    print(f"\n{ERR}  ✖  {text}{RESET}\n")

def msg_warn(text: str) -> None:
    print(f"  {WARN}⚠  {text}{RESET}")

def msg_info(text: str) -> None:
    print(f"  {INFO}◈  {text}{RESET}")

def msg_ok(text: str) -> None:
    print(f"  {OK}✔  {text}{RESET}")

def msg_ollama_missing() -> None:
    tw = _tw()
    print()
    print(f"{ERR}  ✖  ollama not found in PATH — AI suggestions disabled{RESET}")
    print(f"{DIM}{GREY}     install: https://ollama.ai/{RESET}")
    print()

def msg_model_bump(model: str, pid: int) -> None:
    print(f"\n  {PURPLE}⟳{RESET}  {DIM}model {RESET}{CYAN}{model}{RESET}{DIM} reset  ·  PID {pid}{RESET}\n")

def msg_model_loading(model: str) -> None:
    print(f"\n  {CYAN}⏳{RESET}  {DIM}loading {RESET}{CYAN}{model}{RESET}{DIM}…{RESET}\n")

def msg_broken_pipe() -> None:
    print(f"\n  {WARN}⚡{RESET}  {DIM}broken pipe — restarting bash subprocess{RESET}\n")

def msg_ctrlc() -> None:
    print(f"\n  {DIM}{GREY}^C  interrupted{RESET}\n")

def msg_sudo_blocked() -> None:
    print(f"  {WARN}⛔{RESET}  {DIM}sudo is not supported inside llama_term{RESET}")

def msg_chat_enter(model: str) -> None:
    tw = _tw()
    print()
    print(f"{DGREY}{'─' * tw}{RESET}")
    print(f"  {PURPLE}◈{RESET}  {BOLD}{WHITE}entering chat mode{RESET}  {DIM}{GREY}model: {model}   Ctrl+D to exit{RESET}")
    print(f"{DGREY}{'─' * tw}{RESET}")
    print()

def msg_file_included(filename: str) -> None:
    print(f"\n  {OK}📎{RESET}  {DIM}attached:{RESET} {WHITE}{filename}{RESET}\n")

def msg_some_errors() -> None:
    print(f"\n  {WARN}⚠  errors:{RESET}")

def msg_execute_prompt() -> str:
    """Print the execute-choice prompt and return the raw input."""
    print()
    print(
        f"  {DGREY}[{RESET}{YELLOW}y{RESET}{DGREY}]{RESET}{DIM} execute  "
        f"{DGREY}[{RESET}{YELLOW}n{RESET}{DGREY}]{RESET}{DIM} skip  "
        f"{DGREY}[{RESET}{YELLOW}a{RESET}{DGREY}]{RESET}{DIM} always execute{RESET}"
    )
    return input(f"  {BOLD}{CYAN}▶{RESET} ").strip().lower()


# ══════════════════════════════════════════════════════════════════════════════
#  CONTINUATION PROMPT  (multiline / backslash continuation)
# ══════════════════════════════════════════════════════════════════════════════
CONTINUATION_PROMPT = f"{DIM}{DGREY}  ·  {RESET}{DIM}{GREY}"   # append RESET after input()


# ══════════════════════════════════════════════════════════════════════════════
#  STANDALONE DEMO  –  python llama_term_visual.py
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    show_header()
    print()
    show_help()
    print()
    # show sample prompt
    import getpass, socket
    p = build_prompt(getpass.getuser(), socket.gethostname(), os.getcwd())
    # strip ANSI for raw print demo
    print("  Sample prompt (rendered):")
    print()
    for line in p.split("\n"):
        print("  " + line)
    print()
    msg_processing()
    time.sleep(0.4)
    msg_suggestion_header(1.337, 0)
    msg_suggestion_header(2.001, 3)
    msg_executing()
    msg_skipped()
    msg_error("no AI response generated")
    msg_ok("script executed successfully")
    msg_warn("dangerous keyword detected: rm -rf")
    msg_info("always-execute mode is active")
    msg_model_bump("qwen2.5-coder:3b", 12345)
