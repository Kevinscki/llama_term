import os
import subprocess
from pathlib import Path
import shutil
import time
import readline
import shlex
import sys

from prompt_toolkit.formatted_text import ANSI #the ANSI coloring
#from prompt_toolkit.formatted_text import formatted_text as ANSI
#using better prompt handling
from prompt_toolkit import PromptSession
session=PromptSession()


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
LOG_LINE=75
HISTORY_LINES=1  # history size n-lines (larger history not advised)
SENTINEL = "---CMD_END---"
current_dir=Path.cwd()
simulate_typing=True


# Ensure directories exist
BASE_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_DIR.mkdir(parents=True, exist_ok=True)


# Check if ollama exists
ollama_path = shutil.which("ollama")
if not ollama_path:
    print(RED + "Ollama not found. AI suggestions unavailable, Please install it..." + RESET)

#CMD handler
system_env=os.environ.copy()
bashcmd = subprocess.Popen(
    ["/bin/bash"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    cwd=current_dir,
    text=True,
    bufsize=1,
    preexec_fn=os.setpgrp #isolate signals
    )

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
    f"{DIM}{GREY}│{RESET} {WHITE} BUMP(){RESET} {DIM}→ Reset model context (fixes hallucinations/errors){RESET}\n"
    f"{DIM}{GREY}│{RESET} {WHITE} BANNER(){RESET} {DIM}→ Display this banner again{RESET}\n"
    f"{DIM}{GREY}│{RESET} {WHITE} LOAD(){RESET} {DIM}→ Load and prepare your AI model{RESET}\n"
    f"{DIM}{GREY}│{RESET}\n"
    f"{DIM}{GREY}│{RESET}\n"
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
        global ollama_path
        print(CYAN + "Processing..." + RESET)
        print("")

        # Log failed command
        with LOG_FILE.open("a") as f:
            f.write(f"\nUSER: {failed_command}\n\n")

        # Get AI suggestion
        try:
            start_time=time.time()
            with LOG_FILE.open("r") as log_file:
               ai_subprocess=subprocess.Popen(
                    [ollama_path, "run", OLLAMA_MODEL],
                    stdin=log_file,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True, 
                    bufsize=1,
                    )
            
            
            #save to file and print
            with open(TEMP_SCRIPT,'w') as temp_file:
                print("-"*40)
                for chunk in ai_subprocess.stdout:
                        cleanline=chunk.replace("```bash","").replace("```","")
        
                        #simulate word printing for sanity
                        for word in cleanline.split():
                            print(word, end=" ", flush=True)
                            if simulate_typing:
                                time.sleep(0.1)
                        temp_file.write(cleanline)
                        print("")
                        temp_file.flush()
                print("-"*40)
            ai_subprocess.wait()
            end_time=time.time()
            elapsed=end_time-start_time
        except KeyboardInterrupt:
            print("You pressed ctrl+c, that stops stuff")
            return
        except subprocess.CalledProcessError:
            print(RED + "[ERROR] Failed to get AI response. Check your Ollama installation")
            return

        if not TEMP_SCRIPT.exists():
            print(RED + "[ERROR] No AI response generated." + RESET)
            return

        # Display AI suggestion
        print(CYAN + "Suggested code (took "+ f"{elapsed:.6f}" + " seconds to generate):"+ RESET)

        # Ask user if they want to execute
        execute_now=False
        if always_execute:
            chicken=1
        else:
            print("")
            execute_choice = input("Execute AI suggestion? (y/n/a for always): ").lower()
            if execute_choice == "a":
                always_execute = True
            if execute_choice == "y":
                execute_now = True
        if execute_now or always_execute:
            print(GREY + DIM + "[AI ASSISTANT] Executing suggestion..." + RESET+ WHITE)
            TEMP_SCRIPT.chmod(0o755)
            
            # Write TEMP_SCRIPT
            scriptlines = [
                "echo AI__PWD_:$PWD\n",
                "echo AI__END__1\n"
            ]

            with open(TEMP_SCRIPT, 'a') as script:
                script.writelines(scriptlines)

            # Run the script
            global current_dir

            result = subprocess.Popen(
                ["/bin/bash", TEMP_SCRIPT],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            # Read line by line
            endline=True
            while endline:
                line = result.stdout.readline()
                if not line:
                    break
                line = line.rstrip()

                if line.startswith("AI__PWD_:"):

                    current_dir = line.split("AI__PWD_:", 1)[1]
                    # print silently if you want
                    continue

                if line.startswith("AI__END__"):
                    line=""
                    endline=False
                print(line)

            result.stdout.close()
            result.wait()

            with LOG_FILE.open("a") as f:
                with TEMP_SCRIPT.open("r") as temp_file:
                    f.write(temp_file.read())
            if result.returncode != 0:
                with open(TEMP_ERROR_LOG, "w") as f:
                    f.write(str(result.stderr))

                    
                with LOG_FILE.open("a") as f:
                    f.write("MISTAKE:\n")
                    with TEMP_ERROR_LOG.open("r") as err_file:
                        f.write(err_file.read())
                    f.write("\n")
                print(f"{CYAN}Some errors:")
                with TEMP_ERROR_LOG.open("r") as err_file:
                    print(str(err_file.read()))
                    
            TEMP_SCRIPT.unlink(missing_ok=True)
            TEMP_ERROR_LOG.unlink(missing_ok=True)
        else:
            print(YELLOW + "[AI ASSISTANT] Suggestion skipped by user." + RESET)
            TEMP_SCRIPT.unlink(missing_ok=True)
            TEMP_ERROR_LOG.unlink(missing_ok=True)
    except KeyboardInterrupt:
        print("You pressed 'ctrl +c', that stops stuff")
def handle_broken_pipe():
    global bashcmd
    bashcmd = subprocess.Popen(
    ["/bin/bash"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    cwd=current_dir,
    text=True,
    bufsize=1,
    preexec_fn=os.setpgrp #isolate signals
    )
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

# Main loop

while True:
    trim_file(LOG_FILE, LOG_LINE+HISTORY_LINES)  # Keep only the first 67 lines
    last_exit_code = "0"
    prompt_str = f"{GREEN}┌─[{CYAN}{USERNAME}{RESET}@{WHITE}{BOLD}{COMPUTERNAME}{RESET}{GREEN}]─[{WHITE}{BOLD}{current_dir}{RESET}{GREEN}]\n└──╼{YELLOW}{BOLD} $"
    try:
        bashcmd.stdin.write(f"cd {str(current_dir)} \n")
        bashcmd.stdin.flush()
    except BrokenPipeError:
        handle_broken_pipe()
        handle_error(input_command,last_exit_code)
        continue
    
    cmd_lines=[]
    try:
        cmd_line = session.prompt(ANSI(prompt_str))#added ANSI for color
    except KeyboardInterrupt:
        continue
    try:
        while True:
            if cmd_line.endswith("\\") and (len(cmd_line)-len(cmd_line.rstrip("\\")))%2==1:
                # remove trailing backslash and continue
                cmd_lines.append(cmd_line[:-1])
                cmd_line=str(input(f"{DIM}... {RESET}"))
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
    if input_command=="BUMP()":
        proc = subprocess.Popen(
        ["ollama", "run", OLLAMA_MODEL, ""],
        stdout=subprocess.DEVNULL,   # optionally hide output
        stderr=subprocess.DEVNULL,   # optionally hide errors
        stdin=subprocess.DEVNULL     # so it doesn’t wait for stdin
        )
        print(f"{DIM}{YELLOW}The model {OLLAMA_MODEL} has been reset with PID {proc.pid} {RESET}")
        continue
    elif input_command=="LOAD()":
        print(f"{CYAN}{DIM}Loading model..{RESET}")
        proc = subprocess.run(
        f"cat {LOG_FILE} | {ollama_path} run {OLLAMA_MODEL}",
        shell=True,
        stdout=subprocess.DEVNULL,   # optionally hide output
        stderr=subprocess.DEVNULL,   # optionally hide errors
        stdin=subprocess.DEVNULL     # so it doesn’t wait for stdin
        )
        continue
    elif input_command == "BANNER()":
        show_header()
        continue
    else:
        chicken=1
    cmd_lower = input_command.lower()
    if cmd_lower in ("exit", "quit"):
        print ("Goodbye!")
        break
   
    elif cmd_lower == "clear"or cmd_lower == "cls":
        os.system("cls" if os.name == "nt" else "clear")
        continue
    elif cmd_lower.startswith("sudo"):#to fix and alias
        print("Please dont sudo 😭😭😭..")#will improve.. 
        continue
    elif cmd_lower == "help" or cmd_lower =="help()":
        show_help()
        continue

    # Execute command and capture errors
    try:
        # We ask bash to print the exit code ($?) and then the sentinel
        full_cmd = f"{input_command}\necho PY_EXIT__CODE:$?\necho PY_DIRECTORY__:$PWD \necho {SENTINEL}\n"
        try:
            bashcmd.stdin.write(full_cmd)
            bashcmd.stdin.flush()
        except BrokenPipeError:
            handle_broken_pipe()
            handle_error(input_command,last_exit_code)
            continue
        except Exception as e:
            print(e+"[-] stdin did it")
        
        
        while True:
            line = bashcmd.stdout.readline()
            if not line or SENTINEL in line:
                break
            line = line.rstrip("\n")

            # If the line contains our exit code prefix, capture it
            if line.startswith("PY_EXIT__CODE:"):
                last_exit_code = line.replace("PY_EXIT__CODE:", "").strip()
                if "PY_EXIT__CODE:0" in line or not_terminal_counter==1:
                    last_exit_code="0"
                continue # Don't print the exit code line to the user
            if line.startswith("PY_DIRECTORY__:"):
                current_dir = line.replace("PY_DIRECTORY__:", "").strip()
                continue # Don't print the exit code line to the user
            # Stream the output (stdout and stderr merged) normally

            if "command not found" in line and "line" in line and "/bin/bash" in line:
                line=""
            elif "Standard input is not a terminal" in line:
                subprocess.run(
                    input_command,
                    shell=True,
                    cwd=current_dir
                )
                not_terminal_counter=1
                line=""
                continue
            sys.stdout.write(line+"\n")
            sys.stdout.flush()
            not_terminal_counter=0


        # --- ERROR LEVEL LOGIC ---
        if last_exit_code != "0":
            handle_error(input_command, last_exit_code)
            continue

    except KeyboardInterrupt:
        continue
    except Exception as e:
        with USER_ERROR_TEMP.open("w") as f:
            print(e)
        USER_ERROR_TEMP.unlink(missing_ok=True)
