import os
import subprocess
from pathlib import Path
import shutil
import time
import readline
import re
import pty
import sys
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.console import Group
from rich.syntax import Syntax
import termios
from rich.markdown import Markdown
import rich.box as box
from rich import print as rprint
import requests
import json
always_execute = False
from configuration_variables import *
from prompt_toolkit.formatted_text import ANSI #the ANSI coloring


from prompt_toolkit.document import Document
from prompt_toolkit.completion import PathCompleter, Completion, Completer
import signal


history=[]
history.append({"role": "system", "content": open(SYSTEM_PROMPT,'r').read()})



#from prompt_toolkit.formatted_text import formatted_text as ANSI
#using better prompt handling
from prompt_toolkit import PromptSession
console=Console()
class Kompleter(Completer):
    
    def get_completions(self,document,complete_event):
        text_to_parse=document.text_before_cursor
        import shlex

        text_parts=text_to_parse.split()
        if len(text_parts)>0:
            lasts=text_parts[-1]
        else:
            return
        if len(text_parts)==0 or text_parts==" ":
            return
        if len(text_parts) ==1 and text_to_parse[-1]!=" ":
            for command in ["cat","cd","ls","nano","rm",  "vim", "whoami", "id", "clear", "systemctl","source","open","bash"]:
                if command.startswith(text_parts[0]) and text_parts[0]!=command:
                    yield Completion(command,start_position=len(text_parts)-len(command))
            path_completer=PathCompleter(expanduser=True)
            subdocument=Document(text=lasts, cursor_position=len(lasts))
            for comp in path_completer.get_completions(subdocument, complete_event):
                yield Completion(comp.text,start_position=comp.start_position)  
            return

        
        if not text_to_parse[-1]== " ":
            if text_parts[0] == "cd":
                path_completer=PathCompleter(expanduser=True,only_directories=True)
            else:
                path_completer=PathCompleter(expanduser=True)
            subdocument=Document(text=lasts, cursor_position=len(lasts))
            for comp in path_completer.get_completions(subdocument, complete_event):
                yield Completion(comp.text,start_position=0)
            return
session=PromptSession(completer=Kompleter())

def history_standardizer(funct)->str:
    def wrapper(*args,**kwargs)->str:
        if API_TYPE.lower()=="ollama_http":
            return funct(*args,**kwargs)
        elif API_TYPE.lower()=="ollama":
            pass
        elif API_TYPE.lower()=="gemini":
            pass
        return wrapper


def sanitize_for_render(text: str) -> str:
    if text.count("```") % 2 != 0:
        last = text.rfind("```")
        return text[:last].rstrip()
    return text
def build_renderable(full_response: str, risk_counter: int) -> Panel:
    """
    Parse the response into segments: plain markdown and bash code blocks.
    Renders them as a Group so Syntax blocks sit correctly inside the panel.
    """
    segments = []
    lines = full_response.split("\n")

    in_code = False
    lang = "text"
    code_lines = []
    prose_lines = []

    for line in lines:
        if not in_code and line.startswith("```"):
            # flush prose accumulated so far
            if prose_lines:
                prose_text = "\n".join(prose_lines)
                segments.append(Markdown(prose_text, justify="left"))
                prose_lines = []
            lang = line[3:].strip() or "text"
            in_code = True
            code_lines = []

        elif in_code and line.startswith("```"):
            # close code block
            code = "\n".join(code_lines)
            segments.append(Panel(Syntax(code, lang, theme="monokai", word_wrap=True, background_color="default", padding=(1,1)), box=box.ROUNDED, padding=(0,1), border_style="white"))
            in_code = False
            code_lines = []

        elif in_code:
            code_lines.append(line)

        else:
            prose_lines.append(line)

    # flush remaining prose (incomplete response mid-stream)
    if prose_lines:
        prose_text = "\n".join(prose_lines)
        segments.append(Markdown(sanitize_for_render(prose_text), justify="left"))

    # incomplete code block mid-stream — show as plain text so it doesn't break layout
    if in_code and code_lines:
        segments.append(Syntax("\n".join(code_lines), lang, theme="monokai", word_wrap=True))

    title = f"Risky lines found: {risk_counter}" if risk_counter == 0 else f"[bold red]Risky lines found: {risk_counter}[/bold red]"

    

    return Panel(
    Group(*segments) if segments else Markdown("Processing..."),
    title=title,
    padding=(0, 1),
    box=box.ROUNDED,
    border_style="bright_black",  # subtle outer border, won't compete with code panels
)


def ollama_http(messages,model=OLLAMA_MODEL):
    url = "http://localhost:11434/api/chat"
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options":{
            "temperature":0.2,
            "repeat_penalty":1.18,
            "top_p":0.9
            }
    }
    
    with requests.post(url, json=payload, stream=True) as r:
        r.raise_for_status()
        
        for line in r.iter_lines():
            if line:
                chunk = json.loads(line.decode("utf-8"))
                tokens = chunk.get("message",{}).get("content")
                if tokens:
                    yield tokens

import google.generativeai as genai

def ollama_to_gemini(messages: list[dict]) -> tuple[str | None, list[dict]]:
    """
    Convert Ollama chat history to google.generativeai format.
    Returns (system_instruction, history).
    """
    system_instruction = None
    history = []

    for msg in messages:
        role = msg["role"]
        text = msg["content"]

        if role == "system":
            system_instruction = text  # goes into GenerativeModel(), not history
        elif role == "assistant":
            history.append({"role": "model", "parts": [text]})
        else:  # "user"
            history.append({"role": "user", "parts": [text]})

    return system_instruction, history
import google.generativeai as genai

genai.configure(api_key=GEMINI_API)



def gemini_stream(prompt):
    system, contents = ollama_to_gemini(prompt)
    model = genai.GenerativeModel(
        GEMINI_MODEL,
        system_instruction=system
        )
    *prior, last = history
    chat = model.start_chat(history=prior)
    response = chat.send_message(last["parts"][0])
    
    for chunk in response:
        if chunk.text:
            yield chunk.text

# ANSI colors (cross-platform; works on most terminals)
def ai_response(prompt):
    if API_TYPE.lower()=="ollama_http":
        return ollama_http(prompt)

    elif API_TYPE.lower()=="ollama":
        print("no")
    elif API_TYPE.lower()=="gemini":
        print("gemini")
        return gemini_stream(prompt)
# Check if ollama exists
ollama_path = shutil.which("ollama")
if not ollama_path:
    print(RED + "Ollama not found. AI suggestions unavailable, Please install it..." + RESET)

#CMD handler
system_env=os.environ.copy()
bashcmd = subprocess.Popen(
    ["/bin/bash","-s"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    cwd=current_dir,
    text=True,
    bufsize=1,
    preexec_fn=os.setpgrp #isolate signals
    )
bashcmd.stdin.write(f"source {ENV2}\n")
bashcmd.stdin.flush()
bashcmd.stdin.write(f"env >{ENV1}\n")
bashcmd.stdin.flush()
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
    f"{DIM}{GREY}│{RESET} {WHITE} RESET(){RESET} {DIM}→ Reset the shell session\n"
    f"{DIM}{GREY}│{RESET}\n"
    f"{DIM}{GREY}│{RESET}\n"
    f"{DIM}{GREY}└─{RESET} {WHITE}Ctrl+C{RESET} {DIM}→ Cancel current task {RESET}"
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
    """
    keep_a: top critical lines (A)
    keep_c: bottom history lines (C)
    max_lines: total desired cap (optional soft cap)
    """

    with open(filepath, "r") as f:
        all_lines = f.readlines()

    total = len(all_lines)

    # If file is already small enough, do nothing.
    if total <= max_lines+HISTORY_LINES:
        return

    # Split regions
    a_part = all_lines[:max_lines]
    c_part = all_lines[-HISTORY_TRAIL_LINES :] if HISTORY_TRAIL_LINES > 0 and HISTORY_TRAIL_LINES < HISTORY_LINES else []

    new_content = a_part + c_part

    with open(filepath, "w") as f:
        f.writelines(new_content)


def handle_error(failed_command, exit_code):
    try:
        global history 
        
        global ollama_path
        global current_dir
        global risk_counter
        risk_counter=0
        global always_execute
        flagged_lines=[]
        #trim_file(LOG_FILE, LOG_LINE+HISTORY_LINES) ## USE FOR OLD SYSTEM
        if len(history)>=MODEL_CONTEXT_LEN+1:
            history=[history[0]] +history[-MODEL_CONTEXT_LEN:]
        # Legacy, New
        if log_file_type:
            with LOG_FILE.open("a") as f:
                with LOG_FILE.open("r") as log_file:
                    user_content=log_file.read()
        elif another_type:
            user_content=failed_command
        else:
            history.append({"role": "user", "content": failed_command})
            user_content=history
        # Get AI suggestion
        try:
            start_time=time.time()
            
            #save to file and print
            full_response=""
            flagged=-1
            
            with Live(
                Panel(Markdown("Processing..."), padding=(0, 1)),
                refresh_per_second=10,
                transient=False,
                auto_refresh=True,
                console=console
            ) as live:
                full_response = ""
                risk_counter = 0


                # 

                bash_blocks = []

                current_in_code = True

                buffer = ""

                compiled_keywords = [
                    re.compile(rf"\b{re.escape(kw)}\b")
                    for kw in keywords
                ]
                last_render_time=0
                for token in ai_response(user_content):

                    full_response += token
                    buffer += token

                    while "\n" in buffer:

                        line, buffer = buffer.split("\n", 1)

                        if line.startswith("```"):
                            current_in_code = not current_in_code
                            continue

                        if current_in_code:
                            continue
  

                        if any(p.search(line) for p in compiled_keywords):

                            flagged_lines.append(line)
                            risk_counter += 1 

                    live.update(build_renderable(full_response, risk_counter))

            end_time = time.time()
            elapsed = end_time - start_time
            bash_blocks=re.findall(r"```bash\n(.*?)```",full_response,re.DOTALL)
            with open(TEMP_SCRIPT, 'w') as temp_script:
                for block in bash_blocks:
                    temp_script.write(block)
                    temp_script.flush()

            history.append({"role": "assistant", "content": full_response})
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
        if not risk_counter==0:
            print(CYAN + "Suggested code (took "+ f"{elapsed:.6f}" + " seconds to generate), "+RED+"and with "+str(risk_counter)+" RISKY lines."+ RESET)
            print(RED+str('\n'.join(flagged_lines))+RESET)   
        else:
            print(CYAN + "Suggested code (took "+ f"{elapsed:.6f}" + " seconds to generate):"+ RESET)

        # Ask user if they want to execute
        execute_now=False

        if risk_counter>=1:
            always_execute=False
        if not always_execute and bash_blocks:
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
            result = subprocess.Popen(
                ["/bin/bash", TEMP_SCRIPT],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=current_dir,
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
                    os.chdir(current_dir)
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
                    f.write(result.stderr.read())

                    
                with LOG_FILE.open("a") as f:
                    f.write("MISTAKE:\n")
                    with TEMP_ERROR_LOG.open("r") as err_file_log:
                        f.write(err_file_log.read())
                    f.write("\n")
                print(f"{CYAN}Some errors:")
                with TEMP_ERROR_LOG.open("r") as err_file:
                    err_content=err_file.read()
                    print(err_content)
                    err_file.close()
            os.chdir(current_dir)
            TEMP_SCRIPT.unlink(missing_ok=True)
            TEMP_ERROR_LOG.unlink(missing_ok=True)
        else:
            print(YELLOW + "[AI ASSISTANT] Suggestion skipped by user." + RESET)
            TEMP_SCRIPT.unlink(missing_ok=True)
            TEMP_ERROR_LOG.unlink(missing_ok=True)
    except KeyboardInterrupt:
        print(GREY +"You pressed 'ctrl +c', that stops stuff"+RESET)


def lord_bash(wish_is_command):
            global last_exit_code
            global not_terminal_counter
            not_terminal_counter=0
            
            global current_dir

            bashcmd.stdin.write(f"cd {current_dir}\n")
            bashcmd.stdin.flush()
            try:
                
                bashcmd.stdin.write(wish_is_command)
                bashcmd.stdin.flush()
            except BrokenPipeError:
 
                handle_broken_pipe()
                handle_error(wish_is_command,last_exit_code)
                return
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
                    os.chdir(current_dir)
                    continue
                if "command not found" in line and "line" in line and "/bin/bash" in line:
                    line=""
                elif "Standard input is not a terminal" in line or "/bin/bash: error reading input file:" in line:
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
                bashcmd.stdin.write(f"set >{ENV1}\n")
                bashcmd.stdin.flush()
                not_terminal_counter=0

            # --- ERROR LEVEL LOGIC ---
            if last_exit_code != "0":
                handle_error(input_command, last_exit_code)
                return

def handle_broken_pipe():
    global bashcmd
    global tester
    bashcmd = subprocess.Popen(
                ["/bin/bash","-s"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                env=env,
                stderr=subprocess.STDOUT,
                cwd=current_dir,
                text=True,
                bufsize=1,
                preexec_fn=os.setpgrp #isolate signals
                )
 
    tester=subprocess.Popen(
                        ["/bin/bash","-n"],
                        cwd=current_dir,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.DEVNULL,
                        text=True,
                        stderr=subprocess.PIPE
                    )

def include_file(file):
    try:
        with open (f"{os.path.join(current_dir,file)}","r") as include_file:
            INCLUDED_FILE=include_file.read()
    except UnicodeDecodeError:
        basic_file_id=subprocess.run(
                f"file {os.path.join(current_dir,file)}",
                shell=True,
                cwd=current_dir,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE
            )
        INCLUDED_FILE=basic_file_id.stdout
    except Exception as include_error:
        print(include_error)
        return
    print(f"\n{GREY}[+]File: {file} included{RESET}")
    while True:
        
        trim_file(LOG_FILE, LOG_LINE+HISTORY_LINES)
        try:
            file_incl_prompt=f"┌─[{CYAN}{USERNAME}{RESET}@{WHITE}{BOLD}{COMPUTERNAME}{RESET}{GREEN}]─[{WHITE}{BOLD}{current_dir}{RESET}{GREEN}]─[📁]─[{WHITE}{file}{GREEN}]\n└──╼{YELLOW}{BOLD}$"
            
            include_file_prompt = session.prompt(ANSI(f"{file_incl_prompt}"))
            if include_file_prompt.lower()=="exit":
                break
            if not include_file_prompt:
                continue
        
            temporary_one=subprocess.run(
                include_file_prompt,
                shell=True,
                cwd=current_dir,
                stderr=subprocess.PIPE
            )
            if (temporary_one.stderr):
                handle_error(f"REFERENCE FILE:\n[{file}]\n\n{INCLUDED_FILE}\n\n{include_file_prompt}",1)
        except KeyboardInterrupt:
            continue
def handle_bashline(line):
    print("placeholder")
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
    prompt_str = f"{GREEN}┌─[{CYAN}{USERNAME}{RESET}@{WHITE}{BOLD}{COMPUTERNAME}{RESET}{GREEN}]─[{WHITE}{BOLD}{current_dir}{RESET}{GREEN}]\n└──╼{YELLOW}{BOLD} $"
    last_exit_code = "0"
    
    try:
        os.chdir(current_dir)
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
    if not cmd_line:
        continue
    if cmd_line=="RESET()":
        handle_broken_pipe()
        continue
    if cmd_line=="BUMP()":
        history=[]
        history.append({"role": "system", "content": open(SYSTEM_PROMPT,'r').read()})
        print(f"{DIM}cleared{RESET}")
        continue
    elif cmd_line=="LOAD()":
        print(f"{CYAN}{DIM}Loading model..{RESET}")
        history=[{"role": "system", "content": open(SYSTEM_PROMPT,'r').read()}]
        history.append({"role":"user","content":"hello"})
        for _ in ai_response(history):
            pass
        continue
    elif cmd_line == "CHAT()":
        print(f"{GREY}\nYou are interactive chat mode ({OLLAMA_MODEL}), Use {BLUE}{DIM}'ctrl+d' {RESET}{GREY}to {BLUE}{DIM}exit{RESET}\n")
        try:
            subprocess.run(
            [f"/bin/bash","-c",f"ollama run {OLLAMA_MODEL}"],
            text=True
        )
        except KeyboardInterrupt:
                print("you exited")
                continue
    elif cmd_line == "BANNER()":
        show_header()
        continue
    elif cmd_line.startswith("INCLUDE()") and len(cmd_line.split())==2:
        include_file(cmd_line.split()[1])
        continue
    cmd_lower = cmd_line.lower()
    
    if cmd_lower in ("exit", "quit"):
        print ("Goodbye!")
        break
   
    elif cmd_lower == "clear"or cmd_lower == "cls":
        os.system("cls" if os.name == "nt" else "clear")
        continue
    elif cmd_line.startswith("sudo"):#to fix and alias
        print("Please don't sudo 😭😭😭..")#will improve.. 
        continue
    elif cmd_line.startswith("yes"):
        print("yes is not what you think it is")
        continue
    elif cmd_lower == "help" or cmd_lower =="help()":
        show_help()
        continue
    try:
        while True:
            #Hear me out
            continue_counter=False
            try:
                tester=subprocess.Popen(
                        ["/bin/bash", "-n"],
                        cwd=current_dir,
                        text=True,
                        stdin=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        bufsize=1,
                        preexec_fn=os.setpgrp #isolate signals
                    )
                tester.stdin.write(f"{cmd_line}\n")
                tester.stdin.flush()
                stdout, stderr = tester.communicate()
            except BrokenPipeError:
                handle_broken_pipe()

            if "unexpected" in stderr and ("end of file" in stderr or "EOF" in stderr or "token" in stderr):
                cmd_line=f"{cmd_line}\n{str(input(f"{DIM}{DIM}> {RESET}"))}"
                continue_counter=True
            if (cmd_line.endswith("\\") and (len(cmd_line)-len(cmd_line.rstrip("\\")))%2==1):
                # remove trailing backslash and continue
                cmd_line=f"{cmd_line}{str(input(f"{DIM}{DIM}> {RESET}"))}"
                continue_counter=True   
            elif continue_counter:
                continue
            else:
                cmd_lines.append(cmd_line)
                break
        input_command = " ".join(cmd_lines)
        cmd_lines.clear()
    except (KeyboardInterrupt, EOFError):
        continue


    

    # Execute command and capture errors
    try:
        # We ask bash to print the exit code ($?) and then the sentinel
        
        full_cmd = f"{input_command}\necho PY_EXIT__CODE:$?\necho PY_DIRECTORY__:$PWD \necho {SENTINEL}\n"
        lord_bash(full_cmd)

    except KeyboardInterrupt:
        os.killpg(os.getpgid(bashcmd.pid), signal.SIGINT)
        continue
    except Exception as e:



        
        with USER_ERROR_TEMP.open("w") as f:
            print(e)
        USER_ERROR_TEMP.unlink(missing_ok=True)
