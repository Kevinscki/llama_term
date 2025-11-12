##llama_term
This is my fun short script that runs ai (controlled) for running shell commands, the process is simply

***command - > execute***

when that fails

***command -> execute ->ai prompted -> user prompted -> execute the script***

The terminal is not an actual compiled shell, but it emulates whats mostly done in a terminal

The terminal is mostly for UNIX systems (but might also work with windows)

##Settings

you may set 

OLLAMA_MODEL "Default is: qwen2.5-coder:3b"
BASE_DIR
HISTORY_LINES (How many added history to be stored in lines)

read flag.txt will test if the model runs correctly
