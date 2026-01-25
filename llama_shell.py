import os
import subprocess
from pathlib import Path
import shutil
import time
import readline
import shlex

from prompt_toolkit.formatted_text import ANSI #the ANSI coloring
#from prompt_toolkit.formatted_text import formatted_text as ANSI

readline.parse_and_bind("tab: complete") #tab
readline.parse_and_bind("set editing-mode emacs")
# ANSI colors (cross-platform; works on most terminals)
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
USERNAME = os.getenv("USER") or os.getenv("USERNAME")
OLLAMA_MODEL ="qwen2.5-coder:3b"
COMPUTERNAME = os.environ.get("COMPUTERNAME", os.uname().nodename if hasattr(os, "uname") else "PC")
#BASE_DIR = Path.home() / "projects" / "ai" / "llama_term"
BASE_DIR = Path(__file__).resolve().parent
HISTORY_DIR = BASE_DIR / "history"
LOG_FILE = HISTORY_DIR / "log_bash.txt"
USER_ERROR_TEMP = BASE_DIR / "user_errors_temp.txt"
TEMP_ERROR_LOG = BASE_DIR / "error_logs_temp.txt"
TEMP_SCRIPT = BASE_DIR / "temp_script.sh"
HISTORY_LINES=1  # history size n-lines (larger history not advised)
current_dir = Path.cwd()


#using better prompt handling
from prompt_toolkit import PromptSession
session=PromptSession()

#keyboard signal handler
import signal
def handle_sigint(signum,frame):
    print("you did ctrl+c. that stops stuff")

signal.signal(signal.SIGINT, handle_sigint)

# Ensure directories exist
BASE_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_DIR.mkdir(parents=True, exist_ok=True)


# Header
def show_header():
    VARIABLE_NAME="VARIABLE_NAME"
    """Ultra-modern cyberpunk-inspired terminal header with gradient effects"""
    
    # Gradient characters for depth effect
    gradient = ["█", "▓", "▒", "░"]
    
    # Create animated-style top border with gradient
    top_border = f"{CYAN}╭{'─' * 88}╮{RESET}"
    bottom_border = f"{CYAN}╰{'─' * 88}╯{RESET}"
    
    # Futuristic title with neon glow effect
    title_line1 = f"{BOLD}{CYAN}{RESET} {BOLD}{WHITE}            AI{RESET}{CYAN}-{RESET}{BOLD}{WHITE}ASSISTED{RESET} {BOLD}{YELLOW}{RESET} {BOLD}{WHITE}INTERACTIVE SHELL{RESET} {BOLD}{CYAN}{RESET}"
    subtitle = (f"   {RESET} {GREY}Powered by{RESET} {GREY}{BOLD}Ollama{RESET} {GREY}Neural Engine{RESET} \n"
                f"   {RESET} {GREY}by Kevinscki {RESET}{CYAN}https://github.com/Kevinscki/llama_term{RESET}"
                )
                
    # Status indicators with modern icons
    status_line = f"   {DIM}{BLUE}●{RESET} {WHITE}OFFLINE{RESET}  {DIM}|{RESET}  {CYAN}◆{RESET} {WHITE}READY{RESET}  {DIM}|{RESET}  {YELLOW}◆{RESET} {WHITE}BETA{RESET}"
    
    hint = (
    f"{DIM}{GREY}┌─{RESET} {WHITE}HELP{RESET} {DIM}→ Show all available commands{RESET}\n"
    f"{DIM}{GREY}│{RESET} {WHITE} BUMP{RESET} {DIM}→ Reset model context (fixes hallucinations/errors){RESET}\n"
    f"{DIM}{GREY}│{RESET} {WHITE} BANNER(){RESET} {DIM}→ Display this banner again{RESET}\n"
    f"{DIM}{GREY}│{RESET}\n"
    f"{DIM}{GREY}│{RESET} {WHITE} {RESET}{DIM}Variables: {RESET}{WHITE}set NAME=value, {RESET}{DIM}then use {RESET}{WHITE}{{NAME}}{RESET}\n"
    f"{DIM}{GREY}└─{RESET} {WHITE}Ctrl+C{RESET} {DIM}→ Cancel current task{RESET}"
    )


    
    # Separator line with gradient effect
    separator = f"{DIM}{CYAN}{'─' * 90}{RESET}"
    
    # Assemble the header
    print()
    print(top_border)
    print()
    print(title_line1)
    print(subtitle)
    print()
    print(separator)
    print(status_line)
    print(separator)
    print()
    print(hint)
    print()
    print(bottom_border)
    print()
    print(f"   {DIM}{GREY}Terminal is ready...{RESET}")
    print()
show_header()

def trim_file(filepath, max_lines):
    # Read the first `max_lines` lines
    with open(filepath, 'r') as f:
        lines = f.readlines()[:max_lines]
    # Overwrite the file with only those lines
    with open(filepath, 'w') as f:
        f.writelines(lines)
    # Example usage:
always_execute = False

def handle_error(failed_command, exit_code):
    try:
        global always_execute

        print(YELLOW + "Processing..." + RESET)

        # Log failed command
        with LOG_FILE.open("a") as f:
            f.write(f"\nUSER: {failed_command}\n\n")
        # Check if ollama exists
        ollama_path = shutil.which("ollama")
        if not ollama_path:
            print(RED + "[ERROR] Ollama not found. AI suggestions unavailable." + RESET)
            return

        # Get AI suggestion
        try:
            start_time=time.time()
            with TEMP_SCRIPT.open("w") as temp_file:
                subprocess.run(
                    f"cat {LOG_FILE} | {ollama_path} run {OLLAMA_MODEL} | sed 's/```bash//g; s/```//g' > {TEMP_SCRIPT}",
                    shell=True,
                    stdout=temp_file,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    bufsize=1,
                    check=True
                )
            end_time=time.time()
            elapsed=end_time-start_time
        except subprocess.CalledProcessError:
            print(RED + "[ERROR] Failed to get AI response. Check your Ollama installation." + RESET)
            return

        if not TEMP_SCRIPT.exists():
            print(RED + "[ERROR] No AI response generated." + RESET)
            return

        # Display AI suggestion
        print(CYAN + "Suggested code (took "+ f"{elapsed:.6f}" + " seconds to generate):"+ RESET)
        print("-"*40)
        with TEMP_SCRIPT.open("r") as f:
            print(f.read())
        print("-"*40)

        # Ask user if they want to execute
        execute_now=False
        if always_execute:
            chicken=1
        else:
            execute_choice = input("Execute AI suggestion? (y/n/a for always): ").lower()
            if execute_choice == "a":
                always_execute = True
                execute_choice = "y"
            if execute_choice == "y":
                execute_now = True
        if execute_now or always_execute:
            print(GREY + DIM + "[AI ASSISTANT] Executing suggestion..." + RESET+ WHITE)
            TEMP_SCRIPT.chmod(0o755)
            result = subprocess.run(f"bash {TEMP_SCRIPT}", shell=True, stderr=subprocess.PIPE)
            
            
            with LOG_FILE.open("a") as f:
                with TEMP_SCRIPT.open("r") as temp_file:
                    f.write(temp_file.read())
            if result.returncode != 0:
                with open(TEMP_ERROR_LOG, "wb") as f:
                    f.write(result.stderr)
                with LOG_FILE.open("a") as f:
                    f.write("MISTAKE:\n")
                    with TEMP_ERROR_LOG.open("r") as err_file:
                        f.write(err_file.read())
                    f.write("\n")
                print(f"{CYAN}Some errors:")
                with TEMP_ERROR_LOG.open("r") as err_file:
                    print(err_file.read())
            TEMP_SCRIPT.unlink(missing_ok=True)
            TEMP_ERROR_LOG.unlink(missing_ok=True)
        else:
            print(YELLOW + "[AI ASSISTANT] Suggestion skipped by user." + RESET)
            TEMP_SCRIPT.unlink(missing_ok=True)
            TEMP_ERROR_LOG.unlink(missing_ok=True)
    except KeyboardInterrupt:
        print("You pressed 'ctrl +c', that stops stuff")

def show_help():

    print()
    print()
    print("Built-in Commands:")
    print("  help  - Show this help message")
    print("  clear - Clear the screen")
    print("  exit  - Exit the shell")
    print("  quit  - Exit the shell")
    print()
    print("Features:")
    print("  - Executes any system command")
    print("  - On command failure, AI analyzes and suggests fixes")
    print(f"  - Maintains AI learning log in: {LOG_FILE}")
    print("  - Uses Ollama with qwen2.5-coder:3b model (if installed)")
    print()
    print("Logging Policy:")
    print("  - Only failed commands and AI responses are logged")
    print("  - No timestamps to reduce file size")
    print("  - User errors stored in temporary files only")
    print("  - Focus on AI learning and mistakes")
    print()
    print("Requirements:")
    print("  - Ollama installed (https://ollama.ai/) for AI suggestions")
    print("  - qwen2.5-coder:3b model: ollama pull qwen2.5-coder:3b")
    print()
variables = {
    "BASE_DIR": BASE_DIR,
    "LOG_FILE": LOG_FILE,
    "OLLAMA_MODEL": OLLAMA_MODEL
    }
# Main loop
while True:
    trim_file(LOG_FILE, 75+HISTORY_LINES)  # Keep only the first 67 lines
    current_dir=Path.cwd()
    prompt_str = f"{GREEN}┌─[{CYAN}{USERNAME}{RESET}@{WHITE}{BOLD}{COMPUTERNAME}{RESET}{GREEN}]─[{WHITE}{BOLD}{current_dir}{RESET}{GREEN}]\n└──╼{YELLOW}> "
    
    cmd_lines=[]
    try:
        cmd_line = session.prompt(ANSI(prompt_str)).format(**variables)#added ANSI for color
    except KeyboardInterrupt:
        continue
    except KeyError as e:
        print(f"{CYAN}Variable error, you used {YELLOW}{{}} "
      f"{CYAN}-> for variables, use double {YELLOW}{{{{content}}}} {CYAN}for normal braces or JSON {YELLOW}{{{{content:value}}}}"
      f"{CYAN} instead\nerror: {RESET}{e} not a set variable")

        continue
    try:
        while True:
            if cmd_line.endswith("\\"):
                # remove trailing backslash and continue
                cmd_lines.append(cmd_line[:-1])
                cmd_line=str(input(f"{DIM}... {RESET}")).format(**variables)
            else:
                cmd_lines.append(cmd_line)
                break
        input_command = " ".join(cmd_lines)
        cmd_lines.clear()
    except (KeyboardInterrupt, EOFError):
        print()
        continue
    except (EOFError):
        print()
        break

    if not input_command:
        continue
    if input_command=="BUMP":
        proc = subprocess.Popen(
        ["ollama", "run", OLLAMA_MODEL, ""],
        stdout=subprocess.DEVNULL,   # optionally hide output
        stderr=subprocess.DEVNULL,   # optionally hide errors
        stdin=subprocess.DEVNULL     # so it doesn’t wait for stdin
        )
        print(f"{DIM}{YELLOW}The model {OLLAMA_MODEL} has been reset with PID {proc.pid} {RESET}")
        continue
    else: 
        chicken=1
    if input_command == "BANNER()":
        show_header()
        continue
    else:
        chicken=1
    if input_command.startswith("set"):
        var_set=shlex.split(input_command)
        assignments=var_set[1:]
        for item in assignments:
            if "=" not in item:
                print("{YELLOW}{DIM}Nothing set here{RESET}")
                continue  # skip bad assignments
        
            key, value = item.split("=", 1)
            variables[key] = value
    cmd_lower = input_command.lower()
    if cmd_lower in ("exit", "quit"):
        print ("Goodbye!")
        break
    elif input_command.startswith("cd"):
            parts = input_command.split(maxsplit=1)
            if len(parts) == 1:
                target = Path.home()
            else:
                target = Path(parts[1]).expanduser()

            if target.exists() and target.is_dir():
                try:
                    last_dir = Path.cwd()
                    os.chdir(target)
                    current_dir=last_dir
                except PermissionError:
                    print("Permission denied.")
            else:
                print(f"No such directory: {target}")
            continue
            
    elif cmd_lower == "clear"or cmd_lower == "cls":
        os.system("cls" if os.name == "nt" else "clear")
        continue
    elif cmd_lower == "help":
        show_help()
        continue

    # Execute command and capture errors
    try:
        result = subprocess.run(input_command, shell=True, stderr=subprocess.PIPE)
        if result.returncode != 0:
            handle_error(input_command, result.returncode)
    except KeyboardInterrupt:
        continue
    except Exception as e:
        with USER_ERROR_TEMP.open("w") as f:
            f.write(str(e))
        handle_error(input_command, 1)
        USER_ERROR_TEMP.unlink(missing_ok=True)
