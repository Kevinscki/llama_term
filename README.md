# llama_term

An Ai driven python script that operates as Linux terminal through the help from a local ollama model.
![Alt text](screenshotpic.png)

## How it works

The process is simple:

**command → execute**

When that fails:

**command → execute → ai prompted → user prompted → execute the script**

The terminal is not an actual compiled shell, but it emulates what's mostly done in a terminal.

The terminal is mostly for UNIX systems (but might also work with Windows).

## Settings

You may set:

- `OLLAMA_MODEL` (Default: `qwen2.5-coder:3b`)
- `BASE_DIR`
- `HISTORY_LINES` (How many added history to be stored in lines)


## Hallucinations
As the model thought that was the way for smb login (reviewing the scripts can show). Running `BUMP()` in terminal may fix some issues by clearing the context in background (you can modify the `HISTORY_LINES` and modify the prompt in `history/log_bash.txt or history/log_windows.txt` for a tailored or a more accurate experience, but provide some examples for the model).

## Variables

Variables will be stored in persistence just like a linux shell, The ai owever will not access the variables.

## Requirements
Make sure you have `ollama` installed either by snap or from the official website, the model defaults to `qwen2.5-coder:3b`, You can download with `ollama pull`, a model suitable for your machine and needs and replace the `OLLAMA_MODEL` variable inside `llama_shell.py`
## Usage

Just run:

```bash
git clone https://github.com/Kevinscki/llama_term.git
cd llama_term
python3 llama_shell.py
```

Install `pip3 install prompt-toolkit`.
If any issues run this:
```bash
python3 -m venv .env #create the python environment (I dont advise using --break-system-packages)
source ./.env/bin/activate
pip3 install prompt-toolkit
python3 llama_shell.py
```
## Testing

Tell the model to list files or find a file, observe the code after.
