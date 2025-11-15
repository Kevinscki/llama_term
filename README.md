# llama_term

An Ai driven python script that operates as Linux terminal through the help from a local ollama model
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

Running `BUMP()` in terminal may fix some issues.

## Variables

A Python approach has been used instead: the usage of `{}` instead of `# llama_term

A fun short script that runs AI-controlled shell commands.

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

.

## Usage

Just run:

```bash
py llama_shell.py
```

Install `prompt_toolkit` using `pip3`.

## Testing

Read `flag.txt` to test if the model runs correctly.
