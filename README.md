# llama_term

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

## Testing

Tell the model to find the flag (or just read the flag) to test if the model runs correctly.

Feel free to adjust your prompt in the history, will use sqllite3 for next version
