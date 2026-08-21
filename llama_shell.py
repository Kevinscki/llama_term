import os
import subprocess
from pathlib import Path
import shutil
import time
import readline
import re
import sys
import shlex
import json
from datetime import datetime
from rich.console import Console
import termios
import requests
import pty, select
always_execute = False
from configuration_variables import *
from ai_display import stream_response
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.document import Document
from prompt_toolkit.completion import PathCompleter, Completion, Completer
import signal
from prompt_toolkit import PromptSession

#colors
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

ESPRESSO = "\033[38;2;60;30;10m"
MOCHA = "\033[38;2;130;80;40m"
CARAMEL = "\033[38;2;198;140;70m"
CREAM = "\033[38;2;230;210;220m"
LATTE = "\033[38;2;230;210;220m"
FOAM = "\033[38;2;230;210;220m"
CINNAMON = "\033[38;2;180;80;30m"
STEAM = "\033[38;2;160;145;130m"

GREEN = "\033[38;2;120;160;80m"
RED = "\033[38;2;190;70;50m"
YELLOW  = "\033[38;2;210;170;60m"
CYAN = CARAMEL
WHITE = CREAM
GREY = STEAM
BLUE = LATTE

console = Console()


#Completion
class Kompleter(Completer):
    def get_completions(self, document, complete_event):
        text_to_parse = document.text_before_cursor
        if not text_to_parse:
            for command in ["cat", "cd", "ls", "nano", "rm", "vim", "whoami",
                            "id", "clear", "systemctl", "source", "open",
                            "bash", "ASK()", "FLAGS()", "INCLUDE()", "CLEAR()", "BUMP()", "LOAD()",
                            "TOOL()", "ADD_TOOL()", "BANNER()", "RESET()", "HELP"]:
                yield Completion(command, start_position=0)
            return
        

        token_start = len(text_to_parse)
        in_quote = None
        for i in range(len(text_to_parse) - 1, -1, -1):
            char = text_to_parse[i]
            if char in ('"', "'"):
                if in_quote == char:
                    in_quote = None
                elif in_quote is None:
                    in_quote = char
            if in_quote is None and char.isspace():
                break
            token_start = i

        token = text_to_parse[token_start:]
        is_first_token = not text_to_parse[:token_start].strip()

        if is_first_token:
            for command in ["cat", "cd", "ls", "nano", "rm", "vim", "whoami",
                            "id", "clear", "systemctl", "source", "open",
                            "bash", "ASK()", "FLAGS()", "INCLUDE()", "CLEAR()", "BUMP()", "LOAD()",
                            "TOOL()", "ADD_TOOL()", "BANNER()", "RESET()", "HELP"]:
                if command.startswith(token):
                    yield Completion(command, start_position=-len(token))

        if token or text_to_parse[-1] == " ":
            if is_first_token and token == "cd":
                path_completer = PathCompleter(expanduser=True, only_directories=True)
            elif not is_first_token and text_to_parse.split()[0] == "cd":
                path_completer = PathCompleter(expanduser=True, only_directories=True)
            else:
                path_completer = PathCompleter(expanduser=True)

            subdocument = Document(text=token, cursor_position=len(token))
            for comp in path_completer.get_completions(subdocument, complete_event):
                yield Completion(comp.text, start_position=comp.start_position)

session = PromptSession(completer=Kompleter())

#small helpers
def visible_len(text):
    return len(re.sub(r'\x1b\[[0-9;]*[JKm]', '', text))

def extract_bash_blocks(text: str) -> list[str]: #Get bash blocks
    lines = text.split("\n")
    blocks, stack, outer_lang, buf = [], [], None, []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            lang_word = stripped[3:].strip()
            if not stack:
                outer_lang = lang_word or "text"
                stack.append(outer_lang)
                buf = []
            elif lang_word:
                stack.append(lang_word)
                buf.append(line)
            else:
                stack.pop()
                if stack:
                    buf.append(line)
                else:
                    if outer_lang == "bash":
                        blocks.append("\n".join(buf))
                    buf, outer_lang = [], None
        else:
            if stack:
                buf.append(line)
    return blocks


#talk to ollama
def ollama_http(messages, model=OLLAMA_MODEL, url=OLLAMA_URL):
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "think": False,
        "options": {"temperature": 0.2, "repeat_penalty": 1.18, "top_p": 0.9},
    }
    try:
        with requests.post(url, json=payload, stream=True, timeout=OLLAMA_TIMEOUT) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                tokens = chunk.get("message", {}).get("content")
                if tokens:
                    yield tokens
    except requests.RequestException as e:
        raise RuntimeError(f"Ollama request failed: {e}") from e


_gemini_ready = False

def _ensure_gemini():
    global _gemini_ready
    if _gemini_ready:
        return
    if not GEMINI_API:
        raise RuntimeError(
            "GEMINI_API is not set. Put it in .env or the environment "
            "(see .env.example). Rotate any key that was previously hardcoded."
        )
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API)
    _gemini_ready = True
    return genai


#gemini experimental convert.
def convert_to_gemini(messages):
    system_instruction = None
    gemini_history = []

    for msg in messages:
        role = msg.get("role", "user").lower()
        content = msg.get("content", "")

        if role == "system":
            system_instruction = (system_instruction + "\n\n" + content) if system_instruction else content
            continue

        mapped_role = "model" if role in ("assistant", "model") else "user"

        if gemini_history and gemini_history[-1]["role"] == mapped_role:
            gemini_history[-1]["parts"][0] += f"\n\n{content}"
        else:
            gemini_history.append({"role": mapped_role, "parts": [content]})

    return system_instruction, gemini_history


def gemini_stream(prompt):
    genai = _ensure_gemini()
    system, contents = convert_to_gemini(prompt)
    model = genai.GenerativeModel(GEMINI_MODEL, system_instruction=system)

    if not contents:
        return

    history_for_chat = contents[:-1]
    last_message = contents[-1]

    chat = model.start_chat(history=history_for_chat)
    response = chat.send_message(last_message["parts"][0], stream=True)

    for chunk in response:
        if chunk.text:
            yield chunk.text

#Router
def ai_response(prompt):
    if API_TYPE.lower() == "ollama_http":
        return ollama_http(prompt)
    elif API_TYPE.lower() == "gemini":
        return gemini_stream(prompt)
    raise RuntimeError(f"Unknown API_TYPE: {API_TYPE!r}")


#Model should have context (filled in main())
history = []

# Persistent bash — created in start_bash_session() / main()
bashcmd = None

def start_bash_session():
    global bashcmd
    bashcmd = subprocess.Popen(
        ["/bin/bash", "-s"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=current_dir,
        text=True,
        errors="replace",
        bufsize=1,
        preexec_fn=os.setpgrp,
        env=env,
    )
    return bashcmd

#banner
def show_header():
    W = 72

    def row(left="", right="", fill=" "):
        v_left = visible_len(left)
        v_right = visible_len(right)
        inner = left + fill * (W - v_left - v_right) + right
        return f"{MOCHA}│{RESET}{inner}{MOCHA}│{RESET}"

    def rule(l="╭", m="─", r="╮"):
        return f"{MOCHA}{l}{m * W}{r}{RESET}"

    print()
    print(rule("╭", "─", "╮"))
    print(row())
    print(row(
        f"  {CARAMEL}{BOLD}  llama_term{RESET}  "
        f"{DIM}{STEAM}AI-assisted interactive shell{RESET}"
    ))
    print(row(
        f"    {DIM}{STEAM}by Kelvin Rutatina  ·  "
    ))
    print(row())
    print(f"{MOCHA}├{'─' * W}┤{RESET}")
    print(row())
    print(row(f"  {LATTE}Quick reference{RESET}"))
    print(row())

    cmds = [
        ("ASK()",    "Ask the AI — it generates commands from live context"),
        ("FLAGS()",  "Toggle repeat/embed/exitcode context markers"),
        ("BUMP()",   "Reset model context — clears hallucinations"),
        ("LOAD()",   "Warm up and load your AI model"),
        ("TOOL()",   "List or switch active tool"),
        ("BANNER()", "Redisplay this banner"),
        ("RESET()",  "Restart the shell session"),
        ("HELP",     "Show the full command reference"),
        ("Ctrl+C",   "Cancel the current running task"),
    ]
    for cmd, desc in cmds:
        label = f"{CARAMEL}{BOLD}{cmd}{RESET}"
        note  = f"{DIM}{STEAM}{desc}{RESET}"
        pad = W - len(cmd) - len(desc) - 7
        print(f"{MOCHA}│{RESET}  {label}  {LATTE}→{RESET}  {note}{' ' * max(pad, 0)}{MOCHA}│{RESET}")

    print(row())
    print(rule("╰", "─", "╯"))
    print(f"\n  {DIM}{STEAM}Terminal ready.{RESET}\n")


#help text
def show_help():
    W = 68

    def section(title):
        print(f"\n  {CARAMEL}{BOLD}{title}{RESET}")
        print(f"  {MOCHA}{'─' * (len(title))}{RESET}")

    def entry(cmd, desc):
        pad = 18
        print(f"  {CREAM}{cmd:<{pad}}{RESET}{DIM}{STEAM}{desc}{RESET}")

    title = f"  {CARAMEL}{BOLD}  llama_term  —  Command Reference{RESET}"
    v_title = visible_len(title)
    padding = (W + 2) - v_title
    print(f"\n{MOCHA}╭{'─' * (W + 2)}╮{RESET}")
    print(f"{MOCHA}│{RESET}{title}{' ' * padding}{MOCHA}│{RESET}")
    print(f"{MOCHA}╰{'─' * (W + 2)}╯{RESET}")

    section("Built-in Shell Commands")
    entry("help / HELP",    "Show this reference")
    entry("clear / cls",    "Clear the terminal screen")
    entry("exit / quit",    "Close llama_term")

    section("AI Controls")
    entry("ASK() …",        "Ask the model — generates bash from live host/tool context")
    entry("FLAGS()",        "Show context markers (repeat / embed / exitcode)")
    entry("FLAGS() …",      "FLAGS() repeat|embed|exitcode on|off  or  FLAGS() all on|off")
    entry("BUMP()",         "Wipe chat turns — keeps tool prompt + live embeds")
    entry("LOAD()",         "Pre-warm the AI model (faster first response)")
    entry("BANNER()",       "Redisplay the startup banner")
    entry("RESET()",        "Restart the underlying bash session")
    entry("INCLUDE() …",    "Attach file(s): INCLUDE() a b  or  INCLUDE() {a,b}")

    section("How Error Handling Works")
    print(f"  {DIM}{STEAM}When a command exits non-zero, the AI analyses the"
          f" failure and{RESET}")
    print(f"  {DIM}{STEAM}proposes a fix. You choose  y  /  n  /  a (always){RESET}")
    print(f"  {DIM}{STEAM}before anything is executed.{RESET}")
    print(f"  {DIM}{STEAM}ASK() does the same without needing a failed command.{RESET}")
    print(f"  {DIM}{STEAM}Lines flagged as risky are highlighted in"
          f" {CINNAMON}amber{RESET}{DIM}{STEAM} and force a prompt.{RESET}")

    section("Logging")
    print(f"  {DIM}{STEAM}Approved AI scripts append to {LATTE}{LOG_FILE}{RESET}")
    print(f"  {DIM}{STEAM}Do not put secrets in included files sent to cloud providers.{RESET}")
    
    section("Tools")
    entry("TOOL()",          "List available tools")
    entry("TOOL() NAME",     "Switch active tool (e.g. TOOL() GIT)")
    entry("ADD_TOOL() NAME", "AI-draft a new tool, review in editor, save")
    print(f"  {DIM}{STEAM}Tools are markdown system prompts stored in {LATTE}{HISTORY_DIR}{RESET}{DIM}{STEAM}.{RESET}")
    print(f"  {DIM}{STEAM}Current tool: {CARAMEL}{CURRENT_TOOL_NAME}{RESET}")

    section("Setup")
    entry("Ollama",         "https://ollama.ai/")
    entry("Default model",  f"{OLLAMA_MODEL}  (ollama pull {OLLAMA_MODEL})")
    entry("Secrets",        "Copy .env.example → .env (GEMINI_API, etc.)")
    print()

import termios, tty, signal
import fcntl

#pty setup — only used when executing an approved AI script
def make_preexec(fd):
    def preexec():
        os.setsid()
        try:
            fcntl.ioctl(fd, termios.TIOCSCTTY, 0)
        except OSError:
            pass
    return preexec


def run_ai_script_pty(script_path: Path):
    """Run approved AI script in a PTY with cleanup; guard non-TTY stdin."""
    global current_dir
    master_fd, slave_fd = pty.openpty()
    result = None
    old_tty = None
    try:
        result = subprocess.Popen(
            ["/bin/bash", str(script_path)],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            close_fds=True,
            cwd=current_dir,
            preexec_fn=make_preexec(slave_fd),
            env=env,
        )
        os.close(slave_fd)
        slave_fd = -1

        interactive = sys.stdin.isatty() and sys.stdout.isatty()
        if interactive:
            old_tty = termios.tcgetattr(0)
            tty.setraw(0)

        while True:
            try:
                readers = [master_fd] + ([0] if interactive else [])
                r, _, _ = select.select(readers, [], [], 0.1)
            except (ValueError, OSError):
                break
            if master_fd in r:
                try:
                    data = os.read(master_fd, PTY_READ_BYTES)
                except OSError:
                    break
                if not data:
                    break
                lines = data.decode(errors="replace").split("\n")
                clean_lines = []
                for line in lines:
                    if line.startswith(MARKER_AI_PWD):
                        current_dir = line.split(MARKER_AI_PWD, 1)[1].rstrip("\r")
                        try:
                            os.chdir(current_dir)
                        except OSError:
                            pass
                    elif line.startswith(MARKER_AI_END) or line.strip() == MARKER_AI_END:
                        if result.poll() is None:
                            result.terminate()
                    else:
                        clean_lines.append(line)
                clean = "\n".join(clean_lines).encode()
                if clean:
                    os.write(1, clean)
            if interactive and 0 in r:
                try:
                    user_input = os.read(0, PTY_READ_BYTES)
                except OSError:
                    break
                if user_input:
                    os.write(master_fd, user_input)
            if result.poll() is not None:
                break
    finally:
        if old_tty is not None:
            try:
                termios.tcsetattr(0, termios.TCSADRAIN, old_tty)
            except termios.error:
                pass
        try:
            os.close(master_fd)
        except OSError:
            pass
        if slave_fd >= 0:
            try:
                os.close(slave_fd)
            except OSError:
                pass
        if result is not None:
            try:
                result.wait(timeout=5)
            except Exception:
                try:
                    result.kill()
                except Exception:
                    pass
                result.wait()
    return result.returncode if result is not None else -1


LIVE_CONTEXT_MARKER = "# === LIVE HOST / TOOL CONTEXT"

#AI invoke — used on command failure and ASK()
def _messages_for_ai():
    """History view sent to the model, honoring INCLUDE_EMBEDDING."""
    if INCLUDE_EMBEDDING:
        return history
    return [
        m for m in history
        if not (
            m.get("role") == "system"
            and LIVE_CONTEXT_MARKER in m.get("content", "")
        )
    ]


def _fmt_flag(v: bool) -> str:
    return f"{GREEN}on{RESET}" if v else f"{CINNAMON}off{RESET}"


def show_flags():
    print(f"\n{LATTE}AI context flags{RESET}  {DIM}{STEAM}(FLAGS() <name> on|off){RESET}")
    print(f"  {CREAM}repeat{RESET}    {_fmt_flag(REPEAT_EMBEDDING)}"
          f"  {DIM}{STEAM}— re-run embeds every AI call{RESET}")
    print(f"  {CREAM}embed{RESET}     {_fmt_flag(INCLUDE_EMBEDDING)}"
          f"  {DIM}{STEAM}— include LIVE CONTEXT in model prompt{RESET}")
    print(f"  {CREAM}exitcode{RESET}  {_fmt_flag(INCLUDE_EXIT_CODE)}"
          f"  {DIM}{STEAM}— include exit code on failures{RESET}")
    print()


def set_flag(name: str, value: bool) -> bool:
    global REPEAT_EMBEDDING, INCLUDE_EMBEDDING, INCLUDE_EXIT_CODE
    key = name.strip().lower()
    aliases = {
        "repeat": "repeat",
        "repeat_embedding": "repeat",
        "embedding_repeat": "repeat",
        "embed": "embed",
        "embedding": "embed",
        "include_embedding": "embed",
        "include": "embed",
        "exitcode": "exitcode",
        "exit_code": "exitcode",
        "exit": "exitcode",
        "include_exit_code": "exitcode",
    }
    canon = aliases.get(key)
    if canon == "repeat":
        REPEAT_EMBEDDING = value
    elif canon == "embed":
        INCLUDE_EMBEDDING = value
    elif canon == "exitcode":
        INCLUDE_EXIT_CODE = value
    else:
        return False
    return True


def handle_flags(args: list[str]):
    if not args:
        show_flags()
        return

    if len(args) == 1 and args[0].lower() in ("all", "show", "list", "status"):
        show_flags()
        return

    if len(args) == 2 and args[0].lower() == "all":
        val = args[1].lower()
        if val not in ("on", "off", "1", "0", "true", "false"):
            print(f"{STEAM}{DIM}Usage: FLAGS() all on|off{RESET}")
            return
        on = val in ("on", "1", "true")
        set_flag("repeat", on)
        set_flag("embed", on)
        set_flag("exitcode", on)
        show_flags()
        return

    if len(args) != 2:
        print(f"{STEAM}{DIM}Usage: FLAGS() | FLAGS() repeat|embed|exitcode on|off | FLAGS() all on|off{RESET}")
        return

    name, raw = args[0], args[1].lower()
    if raw not in ("on", "off", "1", "0", "true", "false"):
        print(f"{STEAM}{DIM}Value must be on|off{RESET}")
        return
    if not set_flag(name, raw in ("on", "1", "true")):
        print(f"{RED}[ERROR] Unknown flag: {name}{RESET}  "
              f"{DIM}{STEAM}(repeat | embed | exitcode){RESET}")
        return
    show_flags()


def invoke_ai(user_text: str, *, refresh: bool | None = None):
    """Send user_text to the model (with live embeds), stream reply, optional run."""
    global history, current_dir, always_execute
    risk_counter = 0
    flagged_lines = []

    # Decision markers: include embedding? repeat (refresh) embedding?
    do_include = INCLUDE_EMBEDDING
    if refresh is None:
        do_refresh = do_include and REPEAT_EMBEDDING
    else:
        do_refresh = bool(refresh) and do_include

    if do_include and do_refresh:
        try:
            n = refresh_live_context()
            if n:
                print(f"{DIM}{STEAM}Live context refreshed ({n} embed item(s)).{RESET}")
        except NameError:
            pass
        except Exception as e:
            print(f"{STEAM}{DIM}Live context refresh skipped: {e}{RESET}")
    elif do_include and not do_refresh:
        # Keep cached LIVE CONTEXT if present; bootstrap once if missing
        has_live = any(
            m.get("role") == "system" and LIVE_CONTEXT_MARKER in m.get("content", "")
            for m in history
        )
        if not has_live:
            try:
                n = refresh_live_context()
                if n:
                    print(f"{DIM}{STEAM}Live context loaded once ({n} embed item(s)).{RESET}")
            except Exception as e:
                print(f"{STEAM}{DIM}Live context load skipped: {e}{RESET}")
        else:
            print(f"{DIM}{STEAM}Live context reused (repeat=off).{RESET}")
    else:
        print(f"{DIM}{STEAM}Embeddings omitted (embed=off).{RESET}")

    _trim_history()
    history.append({"role": "user", "content": user_text})

    try:
        start_time = time.time()
        full_response, flagged_lines, risk_counter = stream_response(
            ai_response(_messages_for_ai()), keywords=keywords
        )
        elapsed = time.time() - start_time
        bash_blocks = extract_bash_blocks(full_response)

        with open(TEMP_SCRIPT, "w") as tmp:
            tmp.write("\n".join(bash_blocks))
            tmp.write(f'\necho -e "\\n{MARKER_AI_PWD}$(pwd)"')
            tmp.write(f'\necho -e "\\n{MARKER_AI_END}"\n')

        history.append({"role": "assistant", "content": full_response})
    except KeyboardInterrupt:
        print(f"\n{DIM}{STEAM}Cancelled.{RESET}")
        return
    except (subprocess.CalledProcessError, RuntimeError, requests.RequestException, Exception) as e:
        print(f"{RED}[ERROR] AI backend: {e}{RESET}")
        return

    if not TEMP_SCRIPT.exists():
        print(f"{RED}[ERROR] No AI response generated.{RESET}")
        return

    if not bash_blocks:
        print(f"\n{LATTE}Done  ({elapsed:.3f}s)  {DIM}{STEAM}(no bash block to run){RESET}")
        return

    if risk_counter:
        print(f"\n{CARAMEL}Suggestion ready  ({elapsed:.3f}s)  "
              f"{CINNAMON}⚠  {risk_counter} risky line(s):{RESET}")
        print(f"{CINNAMON}" + "\n".join(flagged_lines) + RESET)
        print(f"{DIM}{STEAM}Keyword scan is a convenience aid — not a security guarantee.{RESET}")
    else:
        print(f"\n{LATTE}Suggestion ready  ({elapsed:.3f}s){RESET}")

    execute_now = False
    # High-risk always requires an explicit confirm (FIX.md)
    force_confirm = risk_counter >= 1

    if always_execute and not force_confirm and ALLOW_SESSION_AUTORUN:
        execute_now = True
        print(f"{DIM}{STEAM}Auto-run (session): executing without prompt.{RESET}")
    else:
        print()
        try:
            if force_confirm:
                choice = input(
                    f"  {CINNAMON}HIGH-RISK{RESET} {CREAM}Run it?  "
                    f"{DIM}[y] yes  [n] no{RESET}  › "
                ).lower()
            else:
                choice = input(
                    f"  {CREAM}Run it?  {DIM}[y] yes  [n] no  [a] always (session, non-risky){RESET}  › "
                ).lower()
        except KeyboardInterrupt:
            print(f"\n{DIM}{STEAM}Cancelled.{RESET}")
            TEMP_SCRIPT.unlink(missing_ok=True)
            return
        print()
        if choice == "a" and not force_confirm and ALLOW_SESSION_AUTORUN:
            always_execute = True
            execute_now = True
            print(f"{CINNAMON}Session auto-run ON for non-risky suggestions. Risky lines still prompt.{RESET}")
        elif choice == "y":
            execute_now = True

    if execute_now:
        try:
            rc = run_ai_script_pty(TEMP_SCRIPT)
            try:
                with LOG_FILE.open("a") as f:
                    f.write(f"\n# AI script {datetime.now().isoformat()} rc={rc}\n")
                    f.write(TEMP_SCRIPT.read_text())
            except OSError:
                pass
        except Exception as e:
            print(f"{RED}[ERROR] Script execution failed: {e}{RESET}")
    else:
        print(f"{STEAM}{DIM}Suggestion skipped.{RESET}")

    TEMP_SCRIPT.unlink(missing_ok=True)
    TEMP_ERROR_LOG.unlink(missing_ok=True)


def handle_error(failed_command, exit_code):
    if INCLUDE_EXIT_CODE:
        head = (
            f"Command failed (exit {exit_code}). Fix or replace it using LIVE HOST / TOOL CONTEXT "
            f"when relevant. Emit one ```bash block with real names/IPs from context — no placeholders.\n\n"
        )
    else:
        head = (
            "Command failed. Fix or replace it using LIVE HOST / TOOL CONTEXT when relevant. "
            "Emit one ```bash block with real names/IPs from context — no placeholders.\n\n"
        )
    invoke_ai(f"{head}{failed_command}")


#Reset bash
def handle_broken_pipe():
    global bashcmd
    bashcmd = subprocess.Popen(
        ["/bin/bash", "-s"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=current_dir,
        text=True,
        errors="replace",
        bufsize=1,
        preexec_fn=os.setpgrp,
        env=env,
    )


# Feed cmd + status trailers into the persistent bash. Large pastes go through a
# temp script so we never stall the ~64KiB stdin PIPE against unread stdout.
def _feed_bash_command(cmd_line: str) -> None:
    trailer = (
        f"printf '%s\\n' \"{MARKER_EXIT}$?\"\n"
        f"printf '%s\\n' \"{MARKER_DIR}$PWD\"\n"
        f"printf '%s\\n' \"{MARKER_END}\"\n"
    )
    body = f"{cmd_line}\n{trailer}"
    bashcmd.stdin.write(f"cd {shlex.quote(str(current_dir))}\n")
    if len(body.encode("utf-8", errors="replace")) > LARGE_STDIN_BYTES:
        PASTE_CMD_FILE.write_text(body, encoding="utf-8")
        bashcmd.stdin.write(f"source {shlex.quote(str(PASTE_CMD_FILE))}\n")
    else:
        bashcmd.stdin.write(body)
    bashcmd.stdin.flush()


def lord_bash(cmd_line, file_contents=None, from_includes=False): #The bash runner
    global last_exit_code, current_dir, history
    last_exit_code=0
    not_terminal_counter = 0

    try:
        os.chdir(current_dir)
        bashcmd.stdin.flush()
    except BrokenPipeError:
        handle_broken_pipe()
        return True

    cmd_lines = []
    if not cmd_line:
        return True

    #special cmds
    if cmd_line == "RESET()":
        handle_broken_pipe()
        return True

    if cmd_line == "BUMP()":
        prefix = _system_prefix_len(history) if history else 1
        history = history[:prefix] if history else history
        try:
            refresh_live_context()
        except Exception:
            pass
        print(f"{DIM}{STEAM}Context cleared (tool + live embeds kept).{RESET}")
        return True

    if cmd_line.startswith("ASK()"):
        q = cmd_line[len("ASK()"):].strip()
        if not q:
            print(f"{STEAM}{DIM}Usage: ASK() what should I do with the nginx container{RESET}")
            return True
        invoke_ai(
            "User request (generate the commands yourself from LIVE HOST / TOOL CONTEXT — "
            "do not ask the user to copy/paste invent IDs). "
            "If action is needed, emit one ```bash block using real container names, IPs, "
            "and host facts from context.\n\n"
            f"{q}"
        )
        return True

    if cmd_line.startswith("FLAGS()"):
        handle_flags(cmd_line[len("FLAGS()"):].split())
        return True

    if cmd_line == "LOAD()":
        print(f"{LATTE}{DIM}Warming up model…{RESET}")
        prefix = _system_prefix_len(history) if history else 1
        history = history[:prefix] if history else history
        try:
            refresh_live_context()
        except Exception:
            pass
        history.append({"role": "user", "content": "hello"})
        for _ in ai_response(history):
            pass
        print(f"{CARAMEL}Model ready.{RESET}")
        return True

    if cmd_line == "BANNER()":
        show_header()
        return True

    if cmd_line.startswith("TOOL()"):
        args = cmd_line.split()[1:]
        handle_tool(args)
        return True

    if cmd_line.startswith("ADD_TOOL()"):
        args = cmd_line.split()[1:]
        handle_add_tool(args)
        return True
    #include one or many files
    if cmd_line.startswith("INCLUDE()"):
        files = parse_include_args(cmd_line)
        if files:
            include_file(files)
        else:
            print(f"{STEAM}{DIM}Usage: INCLUDE() file  |  INCLUDE() a b  |  INCLUDE() {{a,b}}{RESET}")
        return True

    cmd_lower = cmd_line.lower()

    if cmd_lower in ("exit", "quit"):
        print(f"\n{CARAMEL}Goodbye. ☕{RESET}\n")
        return False
    if cmd_lower in ("clear", "cls"):
        os.system("cls" if os.name == "nt" else "clear")
        return True
    if cmd_line.startswith("sudo"):
            print(f"{CINNAMON}Please avoid sudo inside llama_term.{RESET}")
            return True
    if cmd_line.startswith("yes"):
        print(f"{STEAM}{DIM}Tip: 'yes' pipes infinite 'y' — pipe to your command instead.{RESET}")
        return True

    if cmd_lower in ("help", "help()"):
        show_help()
        return True

    #multiline?
    try:
        while True:
            try:
                tester = subprocess.Popen(
                    ["/bin/bash", "-n"],
                    cwd=current_dir, text=True,
                    stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE, bufsize=1,
                    preexec_fn=os.setpgrp,
                )
                tester.stdin.write(f"{cmd_line}\n")
                _, stderr = tester.communicate()
            except BrokenPipeError:
                handle_broken_pipe()
                break

            cont = False
            if "unexpected" in stderr and any(t in stderr for t in ("end of file", "EOF", "token")):
                cmd_line += "\n" + input(f"{DIM}> {RESET}")
                cont = True
            if cmd_line.endswith("\\") and (len(cmd_line) - len(cmd_line.rstrip("\\"))) % 2 == 1:
                cmd_line += input(f"{DIM}> {RESET}")
                cont = True
            if not cont:
                cmd_lines.append(cmd_line)
                break
        input_command = " ".join(cmd_lines)
        cmd_lines.clear()
    except (KeyboardInterrupt, EOFError):
        return True

    #run it (large pastes use a temp script — see _feed_bash_command)
    try:
        _feed_bash_command(cmd_line)
    except BrokenPipeError:
        handle_broken_pipe()
        handle_error(input_command, last_exit_code)
        return True
    except Exception as e:
        print(e)
        return True

    while True:
        try:
            line = bashcmd.stdout.readline()
            if not line:
                break
            raw = line.rstrip("\n")
            # Exact trailer records only (session-random markers)
            if raw == MARKER_END:
                break
            if raw.startswith(MARKER_EXIT):
                try:
                    last_exit_code = int(raw[len(MARKER_EXIT):].strip() or "0")
                except ValueError:
                    last_exit_code = 1
                if not_terminal_counter == 1:
                    last_exit_code = 0
                continue
            if raw.startswith(MARKER_DIR):
                new_dir = raw[len(MARKER_DIR):].strip()
                if new_dir:
                    current_dir = new_dir
                    try:
                        os.chdir(current_dir)
                    except OSError:
                        pass
                continue
            if "command not found" in raw and "/bin/bash" in raw:
                continue
            if "Standard input is not a terminal" in raw or "/bin/bash: error reading input file:" in raw:
                subprocess.run(input_command, shell=True, cwd=current_dir, env=env)
                not_terminal_counter = 1
                continue
            sys.stdout.write(raw + "\n")
            sys.stdout.flush()
            not_terminal_counter = 0
        except KeyboardInterrupt:
            try:
                os.killpg(bashcmd.pid, signal.SIGINT)
            except Exception:
                pass
            return True
    if last_exit_code != 0:
        handle_error(input_command, last_exit_code)

    return True


#expand {a,b,c} tokens
def expand_brace_token(tok):
    if tok.startswith("{") and tok.endswith("}") and "," in tok:
        return [p.strip() for p in tok[1:-1].split(",") if p.strip()]
    return [tok]

#INCLUDE() args: spaces, quotes, or {a,b}
def parse_include_args(cmd_line):
    rest = cmd_line[len("INCLUDE()"):].strip()
    if not rest:
        return []
    try:
        parts = shlex.split(rest)
    except ValueError:
        parts = rest.split()
    files = []
    for p in parts:
        files.extend(expand_brace_token(p))
    return files

#read one path for include — capped + sensitive-path gate
def _resolve_include_path(file: str) -> Path:
    p = Path(file).expanduser()
    if not p.is_absolute():
        p = Path(current_dir) / p
    return p.resolve()


def _path_looks_sensitive(path: Path) -> bool:
    text = str(path).lower()
    return any(m in text for m in SENSITIVE_PATH_MARKERS)


def _read_include_blob(file):
    path = _resolve_include_path(file)
    try:
        if not path.is_file():
            print(f"{RED}[ERROR] Not a file: {path}{RESET}")
            return None
        if _path_looks_sensitive(path):
            print(f"{CINNAMON}[!] Sensitive path: {path}{RESET}")
            try:
                ok = input(f"  {CREAM}Include anyway? [y/N] › {RESET}").lower()
            except KeyboardInterrupt:
                return None
            if ok != "y":
                print(f"{STEAM}{DIM}Skipped.{RESET}")
                return None
        data = path.read_text(errors="replace")
        orig_len = len(data)
        truncated = False
        if MAX_INCLUDE_BYTES is not None and orig_len > MAX_INCLUDE_BYTES:
            data = data[:MAX_INCLUDE_BYTES] + f"\n# [truncated at {MAX_INCLUDE_BYTES} chars]"
            truncated = True
        print(
            f"{DIM}{STEAM}  {path}  ({orig_len} chars"
            f"{', truncated' if truncated else ''}){RESET}"
        )
        return data
    except UnicodeDecodeError:
        result = subprocess.run(
            ["file", str(path)],
            cwd=current_dir,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        return (result.stdout or b"").decode(errors="replace")
    except Exception as e:
        print(e)
        return None

#attach file(s) then loop until exit
def include_file(files):
    global prompt_str
    if isinstance(files, str):
        files = [files]

    provider = API_TYPE.lower()
    if provider == "gemini":
        print(
            f"{CINNAMON}[!] Active AI provider: Gemini (cloud). "
            f"Included file text may leave this machine.{RESET}"
        )
    else:
        print(f"{DIM}{STEAM}Active AI provider: {provider}{RESET}")

    blobs = []
    for file in files:
        data = _read_include_blob(file)
        if data is None:
            continue
        blobs.append((file, data))
        print(f"{LATTE}[+] File attached: {CREAM}{file}{RESET}")

    if not blobs:
        print(f"{RED}[ERROR] No files attached.{RESET}")
        return

    label = ", ".join(f for f, _ in blobs)
    combined = "\n\n".join(f"REFERENCE FILE:\n[{f}]\n\n{c}" for f, c in blobs)

    while True:
        prompt = (
            f"{MOCHA}┌─[{CARAMEL}{USERNAME}{RESET}{ESPRESSO}@{RESET}{CREAM}{BOLD}{COMPUTERNAME}{RESET}{MOCHA}]"
            f"─[{CREAM}{BOLD}{current_dir}{RESET}{MOCHA}]─[📁 {LATTE}{label}{MOCHA}]\n"
            f"└──╼{CARAMEL}{BOLD} $ "
        )
        try:
            cmd = session.prompt(ANSI(prompt))
        except KeyboardInterrupt:
            continue
        if cmd.lower() == "exit":
            break
        if not cmd:
            continue
        result = subprocess.run(
            cmd, shell=True, cwd=current_dir,
            capture_output=True, text=True, errors="replace", env=env,
        )
        if result.stdout:
            sys.stdout.write(result.stdout)
            if not result.stdout.endswith("\n"):
                sys.stdout.write("\n")
            sys.stdout.flush()
        if result.stderr:
            sys.stderr.write(result.stderr)
            sys.stderr.flush()
        # FIX.md: invoke AI on non-zero exit, not merely stderr noise
        if result.returncode != 0:
            if provider == "gemini":
                print(
                    f"{CINNAMON}[!] About to send included file content + failed command "
                    f"to Gemini.{RESET}"
                )
                try:
                    go = input(f"  {CREAM}Continue? [y/N] › {RESET}").lower()
                except KeyboardInterrupt:
                    continue
                if go != "y":
                    print(f"{STEAM}{DIM}AI call skipped.{RESET}")
                    continue
            handle_error(f"{combined}\n\n{cmd}", result.returncode)

def list_tools():
    tools = sorted(p.stem for p in HISTORY_DIR.glob("*.md") if p.stem != "BASH_LEGACY")
    if not tools:
        print(f"{STEAM}{DIM}No tools found.{RESET}")
        return
    print(f"\n{LATTE}Available tools:{RESET}")
    for t in tools:
        marker = f" {CARAMEL}(active){RESET}" if t.upper() == CURRENT_TOOL_NAME else ""
        print(f"  {CREAM}{t}{RESET}{marker}")
    print()

HELP = {
    "TOOL": (
        f"  {CREAM}TOOL(){RESET}                 list available tools\n"
        f"  {CREAM}TOOL() LIST{RESET}            list available tools\n"
        f"  {CREAM}TOOL() NAME{RESET}            switch to tool NAME (e.g. TOOL() GIT)\n"
    ),
    "ADD_TOOL": (
        f"  {CREAM}ADD_TOOL() NAME{RESET}                switch on a blank/default tool draft\n"
        f"  {CREAM}ADD_TOOL() NAME description{RESET}    let the AI draft NAME from a description\n"
        f"  {DIM}{STEAM}NAME must be letters/numbers/underscore only{RESET}\n"
    ),
}
 
 
def print_help(name: str):
    text = HELP.get(name.upper())
    if not text:
        return
    print(f"\n{LATTE}Usage — {name.upper()}(){RESET}")
    print(text)
 
#Switching tool 
def handle_tool(args: list[str]):
    if not args:
        list_tools()
        return
    sub = args[0].upper()
    if sub == "LIST" or sub =="LS":
        list_tools()
        return
    if not TOOL_NAME_RE.match(args[0]):
        print(f"{RED}[ERROR] Invalid tool name.{RESET}")
        print_help("TOOL")
        return
    tool_path = HISTORY_DIR / f"{sub}.md"
    if not tool_path.exists():
        print(f"{RED}[ERROR] No such tool: {args[0].upper()}{RESET}")
        print_help("TOOL")
        return
    swap_tool(args[0])
 

#embeds


def embed_string(item: dict) -> str:
    return str(item.get("value", ""))


def embed_time(item: dict) -> str:
    return datetime.now().isoformat(timespec="seconds")



ALLOWED_DIRS = [
    HISTORY_DIR.resolve(),
    (Path.home() / "temp" / "ideas").resolve(),
]

def _safe_resolve(full_path: str) -> Path | None:
    candidate = Path(full_path).expanduser().resolve()
    for allowed in ALLOWED_DIRS:
        if candidate == allowed or allowed in candidate.parents:
            return candidate
    return None

def embed_file(item: dict) -> str | None:
    rel_path = item.get("path", "")
    path = _safe_resolve(rel_path)

    if path is None:
        print(f"{RED}[WARNING] Path outside allowed roots, skipped: {rel_path}{RESET}")
        return None
    if not path.is_file():
        print(f"{RED}[WARNING] File not found, skipped: {rel_path}{RESET}")
        return None

    data = path.read_text(errors="replace")
    # Prefer per-item max_bytes; else MAX_FILE_BYTES (None = unlimited)
    max_bytes = item.get("max_bytes", MAX_FILE_BYTES)
    if max_bytes is not None and len(data) > max_bytes:
        data = data[:max_bytes] + f"\n# [truncated at {max_bytes} chars]"

    return f"# --- file: {rel_path} ---\n{data}"


def embed_tree(item: dict) -> str | None:
    rel_path = item.get("path", ".")
    depth = item.get("depth", MAX_TREE_DEPTH)
    root = _safe_resolve(rel_path)

    if root is None:
        print(f"{RED}[WARNING] Path outside allowed roots, skipped: {rel_path}{RESET}")
        return None
    if not root.is_dir():
        print(f"{RED}[WARNING] Not a directory, skipped: {rel_path}{RESET}")
        return None

    lines = []

    def walk(dir_path: Path, prefix: str, level: int):
        if depth is not None and level > depth:
            return
        try:
            entries = sorted(dir_path.iterdir(), key=lambda p: (p.is_file(), p.name))
        except PermissionError:
            return
        for entry in entries:
            lines.append(f"{prefix}{entry.name}{'/' if entry.is_dir() else ''}")
            if entry.is_dir():
                walk(entry, prefix + "  ", level + 1)

    walk(root, "", 1)
    label = f"depth {depth}" if depth is not None else "full depth"
    return f"# --- tree: {rel_path} ({label}) ---\n" + "\n".join(lines)





def embed_bash(item: dict) -> str | None:
    binary = item.get("command", "")
    args = tuple(item.get("args", []))

    allowed_arg_sets = ALLOWED_EMBED_COMMANDS.get(binary) if isinstance(ALLOWED_EMBED_COMMANDS, dict) else None
    if allowed_arg_sets is None or args not in allowed_arg_sets:
        print(f"{RED}[WARNING] '{binary} {' '.join(args)}' not in allowlist, skipped.{RESET}")
        return None

    result = subprocess.run(
        [binary, *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=15,
    )
    out = (result.stdout or "").strip()
    return f"# --- bash: {binary} {' '.join(args)} ---\n{out}"


def embed_script(item: dict) -> str | None:
    """Run a named read-only snapshot from ALLOWED_EMBED_SCRIPTS."""
    name = str(item.get("name", "")).strip()
    scripts = ALLOWED_EMBED_SCRIPTS if isinstance(ALLOWED_EMBED_SCRIPTS, dict) else {}
    body = scripts.get(name)
    if not body:
        print(f"{RED}[WARNING] Unknown embed script: {name!r} — skipped.{RESET}")
        return None
    result = subprocess.run(
        ["/bin/bash", "-c", body],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=30,
        cwd=str(current_dir),
    )
    out = (result.stdout or "").strip()
    return f"# --- script: {name} ---\n{out}"


_EMBED_HANDLERS = {
    "string": embed_string,
    "time":   embed_time,
    "file":   embed_file,
    "tree":   embed_tree,
    "bash":   embed_bash,
    "script": embed_script,
}

def resolve_embed_item(item: dict) -> str | None:
    kind = str(item.get("type", "")).strip().lower()
    handler = _EMBED_HANDLERS.get(kind)
    if handler is None and kind == "script":
        handler = embed_script  # hard fallback if dict drifted
    if handler is None:
        print(f"{RED}[WARNING] Unknown embed type: {kind!r} — skipped.{RESET}")
        return None
    return handler(item)


def _tool_prompt_and_embed_items(tool_path: Path):
    """Split tool markdown into prompt text + embed_json context list."""
    raw = tool_path.read_text()
    match = re.search(r"```embed_json\s*(.*?)\s*```", raw, re.DOTALL)
    content = re.sub(
        r"```embed_json\s*.*?\s*```",
        "# May include useful embeddings or not",
        raw,
        flags=re.DOTALL,
    )
    items = []
    if match:
        try:
            payload = json.loads(match.group(1))
            ctx = payload.get("context", [])
            if isinstance(ctx, list):
                items = [i for i in ctx if isinstance(i, dict)]
            else:
                print(f"{RED}[WARNING] 'context' must be a list — skipping embeds.{RESET}")
        except json.JSONDecodeError as e:
            print(f"{RED}[ERROR] Malformed embed_json block, skipping embeds: {e}{RESET}")
    return content, items


def _run_embed_items(context_items: list) -> list[str]:
    chunks = []
    for item in context_items:
        result = resolve_embed_item(item)
        if result:
            chunks.append(result)
    return chunks


def _system_prefix_len(hist: list) -> int:
    """How many leading system messages to always keep (tool prompt + embeds)."""
    n = 0
    for msg in hist:
        if msg.get("role") == "system":
            n += 1
        else:
            break
    return max(n, 1)


def _trim_history():
    """Keep leading system messages + last MODEL_CONTEXT_LEN turns."""
    global history
    prefix = _system_prefix_len(history)
    tail_budget = MODEL_CONTEXT_LEN
    if len(history) <= prefix + tail_budget:
        return
    history = history[:prefix] + history[-(tail_budget):]


def refresh_live_context() -> int:
    """Re-run current tool embeds and upsert a LIVE CONTEXT system message.

    Returns number of embed chunks embedded (0 if none).
    """
    global history
    tool_path = CURRENT_TOOL_PATH if isinstance(CURRENT_TOOL_PATH, Path) else Path(CURRENT_TOOL_PATH)
    if not tool_path.exists():
        return 0
    _, items = _tool_prompt_and_embed_items(tool_path)
    if not items:
        return 0
    chunks = _run_embed_items(items)
    if not chunks:
        return 0
    stamp = datetime.now().isoformat(timespec="seconds")
    blob = (
        f"{LIVE_CONTEXT_MARKER} (refreshed {stamp}) ===\n"
        "Use these LIVE facts when generating commands. "
        "Prefer real container names, IPs, and paths from below — never invent placeholders.\n\n"
        + "\n\n".join(chunks)
    )
    # Replace existing live-context system msg, or insert after tool prompt
    replaced = False
    for i, msg in enumerate(history):
        if msg.get("role") == "system" and LIVE_CONTEXT_MARKER in msg.get("content", ""):
            history[i] = {"role": "system", "content": blob}
            replaced = True
            break
    if not replaced:
        # After first system (tool prompt); before any user/assistant turns
        insert_at = 1 if history and history[0].get("role") == "system" else 0
        history.insert(insert_at, {"role": "system", "content": blob})
    return len(chunks)


#swap tool md
def swap_tool(name: str):
    global history, CURRENT_TOOL_NAME, CURRENT_TOOL_PATH

    name = name.strip().upper()
    if not TOOL_NAME_RE.match(name):
        print(f"{RED}[ERROR] Invalid tool name — letters, numbers, underscore only.{RESET}")
        return

    tool_path = HISTORY_DIR / f"{name}.md"
    if not tool_path.exists():
        print(f"{RED}[ERROR] No such tool: {name}.  Try TOOL() LIST or ADD_TOOL() {name}{RESET}")
        return

    content, items = _tool_prompt_and_embed_items(tool_path)
    CURRENT_TOOL_NAME = name
    CURRENT_TOOL_PATH = tool_path
    history = [{"role": "system", "content": content}]

    n = 0
    if items:
        n = refresh_live_context()

    print(
        f"{CARAMEL}Switched to tool: {CREAM}{name}{RESET}  "
        f"{DIM}{STEAM}(embedded {n}/{len(items)} item(s)){RESET}"
    )




#add tool

def _open_in_editor(path):
    old_tty = termios.tcgetattr(0)
    try:
        subprocess.run([EDITOR, str(path)])
    finally:
        termios.tcsetattr(0, termios.TCSADRAIN, old_tty)


def _draft_default_tool_md(name: str, description: str) -> str:
    return (
        f"# {name} tool\n\n"
        f"You are a specialized assistant for: {description or name}.\n\n"
        f"- Explain syntax and commands clearly for learners.\n"
        f"- Prefer safe, non-destructive examples.\n"
        f"- Do not suggest destructive or irreversible commands without warning.\n"
        f"EOTOOL\n"
    )


def _ask_ollama_for_tool(name: str, description: str) -> str:
    messages = [
        {"role": "system", "content": TOOL_META_PROMPT},
        {"role": "user", "content": f"Tool name: {name}\nDescription: {description or '(none given, infer from name)'}"},
    ]
    chunks = []
    try:
        for token in ollama_http(messages):
            chunks.append(token)
    except Exception as e:
        print(f"{RED}[ERROR] Ollama call failed: {e}{RESET}")
        return ""
    draft = "".join(chunks).strip()
    if not draft.rstrip().endswith("EOTOOL"):
        draft += "\nEOTOOL"
    return draft


def handle_add_tool(args: list[str]):
    if not args:
        print(f"{RED}[ERROR] Missing tool name.{RESET}")
        print_help("ADD_TOOL")
        return
 
    name = args[0].strip().upper()
    if not TOOL_NAME_RE.match(name):
        print(f"{RED}[ERROR] Invalid tool name.{RESET}")
        print_help("ADD_TOOL")
        return
    description = " ".join(args[1:]).strip()

    final_path = HISTORY_DIR / f"{name}.md"
    temp_path = HISTORY_DIR / f"{name}.md.temp"
    ai_path = HISTORY_DIR / f"{name}.md.temp.ai"

    if final_path.exists():
        try:
            choice = input(
                f"  {CREAM}Tool '{name}' already exists. Overwrite?  [y/N]{RESET}  › "
            ).lower()
        except KeyboardInterrupt:
            print(f"\n{DIM}{STEAM}Cancelled.{RESET}")
            return
        if choice != "y":
            print(f"{STEAM}{DIM}Cancelled.{RESET}")
            return
        backup = HISTORY_DIR / f"{name}.md.bak"
        backup.write_text(final_path.read_text())

    temp_path.write_text(_draft_default_tool_md(name, description))

    print(f"{LATTE}{DIM}Asking model to draft tool prompt…{RESET}")
    ai_draft = _ask_ollama_for_tool(name, description)
    if ai_draft:
        ai_path.write_text(ai_draft)
        print(f"{CARAMEL}AI draft ready.{RESET}\n")
        print(f"{DIM}{STEAM}{ai_draft}{RESET}\n")
    else:
        print(f"{STEAM}{DIM}No AI draft available — falling back to default template.{RESET}")

    use_ai = False
    if ai_draft:
        try:
            choice = input(
                f"  {CREAM}Edit which version?  [a] AI draft  [d] default  › {RESET}"
            ).lower()
        except KeyboardInterrupt:
            print(f"\n{DIM}{STEAM}Cancelled.{RESET}")
            temp_path.unlink(missing_ok=True)
            ai_path.unlink(missing_ok=True)
            return
        use_ai = (choice == "a")

    edit_path = ai_path if use_ai else temp_path

    print(f"{DIM}{STEAM}Opening in {EDITOR} — save and exit to finalize.{RESET}")
    _open_in_editor(edit_path)

    content = edit_path.read_text().strip()
    if not content:
        print(f"{STEAM}{DIM}Empty file — tool not created.{RESET}")
        temp_path.unlink(missing_ok=True)
        ai_path.unlink(missing_ok=True)
        return

    final_path.write_text(content)
    temp_path.unlink(missing_ok=True)
    ai_path.unlink(missing_ok=True)
    print(f"{CARAMEL}Tool saved: {CREAM}{name}.md{RESET}  {DIM}{STEAM}(use TOOL() {name} to switch){RESET}")


def main():
    global history, bashcmd, current_dir

    start_bash_session()
    show_header()
    print(f"{DIM}{STEAM}Provider: {API_TYPE}  ·  runtime: {RUNTIME_DIR}{RESET}")
    if API_TYPE.lower() == "gemini" and not GEMINI_API:
        print(f"{CINNAMON}[!] GEMINI_API unset — set it in .env before using Gemini.{RESET}")

    # Apply default tool prompt + live embeds
    try:
        _content, _items = _tool_prompt_and_embed_items(Path(CURRENT_TOOL_PATH))
        history = [{"role": "system", "content": _content}]
        if _items:
            _n = refresh_live_context()
            print(f"{DIM}{STEAM}Live context ready ({_n} embed item(s) for {CURRENT_TOOL_NAME}).{RESET}")
    except Exception as e:
        history = [{"role": "system", "content": Path(SYSTEM_PROMPT).read_text()}]
        print(f"{STEAM}{DIM}Live context init skipped: {e}{RESET}")

    while True:
        prompt_str = (
            f"{MOCHA}┌─[{CARAMEL}{USERNAME}{RESET}{ESPRESSO}@{RESET}{STEAM}{BOLD}{COMPUTERNAME}{RESET}{MOCHA}]"
            f"─[{CREAM}{BOLD}{current_dir}{RESET}{MOCHA}]\n"
            f"└──╼{CARAMEL}{BOLD} $ "
        )

        try:
            os.chdir(current_dir)
            bashcmd.stdin.flush()
        except BrokenPipeError:
            handle_broken_pipe()
            continue
        except Exception:
            handle_broken_pipe()
            continue

        try:
            cmd_line = session.prompt(ANSI(prompt_str))
        except KeyboardInterrupt:
            continue
        except EOFError:
            print(f"\n{CARAMEL}Goodbye. ☕{RESET}\n")
            break
        if not cmd_line:
            continue

        try:
            if not lord_bash(cmd_line):
                break
        except KeyboardInterrupt:
            continue


if __name__ == "__main__":
    main()

