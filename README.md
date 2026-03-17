# Web OSINT Tool

<<<<<<< Updated upstream
<<<<<<< Updated upstream
An Ai driven python script that operates as Linux terminal through the help from a local ollama model.
![Alt text](screenshotpic.png)
=======
This repository contains tools and scripts for conducting OSINT (Online Security Investigation) on web targets. This guide will help you get started.
>>>>>>> Stashed changes
=======
This repository contains tools and scripts for conducting OSINT (Online Security Investigation) on web targets. This guide will help you get started.
>>>>>>> Stashed changes

## Installation

1. **Clone the Repository**:
   
   git clone https://github.com/yourusername/web-osint-tool.git
   cd web-osint-tool
   

2. **Dependencies**:
   Ensure you have the necessary dependencies installed. You can install them using 
Usage:   
  pip <command> [options]

Commands:
  install                     Install packages.
  download                    Download packages.
  uninstall                   Uninstall packages.
  freeze                      Output installed packages in requirements format.
  inspect                     Inspect the python environment.
  list                        List installed packages.
  show                        Show information about installed packages.
  check                       Verify installed packages have compatible dependencies.
  config                      Manage local and global configuration.
  search                      Search PyPI for packages.
  cache                       Inspect and manage pip's wheel cache.
  index                       Inspect information available from package indexes.
  wheel                       Build wheels from your requirements.
  hash                        Compute hashes of package archives.
  completion                  A helper command used for command completion.
  debug                       Show information useful for debugging.
  help                        Show help for commands.

General Options:
  -h, --help                  Show help.
  --debug                     Let unhandled exceptions propagate outside the main subroutine, instead of logging them to stderr.
  --isolated                  Run pip in an isolated mode, ignoring environment variables and user configuration.
  --require-virtualenv        Allow pip to only run in a virtual environment; exit with an error otherwise.
  --python <python>           Run pip with the specified Python interpreter.
  -v, --verbose               Give more output. Option is additive, and can be used up to 3 times.
  -V, --version               Show version and exit.
  -q, --quiet                 Give less output. Option is additive, and can be used up to 3 times (corresponding to WARNING, ERROR, and CRITICAL logging levels).
  --log <path>                Path to a verbose appending log.
  --no-input                  Disable prompting for input.
  --proxy <proxy>             Specify a proxy in the form scheme://[user:passwd@]proxy.server:port.
  --retries <retries>         Maximum number of retries each connection should attempt (default 5 times).
  --timeout <sec>             Set the socket timeout (default 15 seconds).
  --exists-action <action>    Default action when a path already exists: (s)witch, (i)gnore, (w)ipe, (b)ackup, (a)bort.
  --trusted-host <hostname>   Mark this host or host:port pair as trusted, even though it does not have valid or any HTTPS.
  --cert <path>               Path to PEM-encoded CA certificate bundle. If provided, overrides the default. See 'SSL Certificate Verification' in pip documentation for more information.
  --client-cert <path>        Path to SSL client certificate, a single file containing the private key and the certificate in PEM format.
  --cache-dir <dir>           Store the cache data in <dir>.
  --no-cache-dir              Disable the cache.
  --disable-pip-version-check
                              Don't periodically check PyPI to determine whether a new version of pip is available for download. Implied with --no-index.
  --no-color                  Suppress colored output.
  --no-python-version-warning
                              Silence deprecation warnings for upcoming unsupported Pythons.
  --use-feature <feature>     Enable new functionality, that may be backward incompatible.
  --use-deprecated <feature>  Enable deprecated functionality, that will be removed in the future. or your package manager.

<<<<<<< Updated upstream
<<<<<<< Updated upstream
The terminal is not an actual compiled shell, but it emulates what's mostly done in a terminal.

The terminal is mostly for UNIX systems (but might also work with Windows).

## Settings

You may set:

- `OLLAMA_MODEL`
- `BASE_DIR`
- `HISTORY_LINES`


## Hallucinations
As the model can get to think something weird (reviewing the scripts given can show). Running `BUMP()` in terminal may fix some issues by clearing the context in background. You can modify the `HISTORY_LINES` and modify the prompt in `history/log_bash.txt or history/log_windows.txt` for a tailored or a more accurate experience, but provide some examples for the model.
You can also preload the model by typing `LOAD()` before sending any other prompts.
## Variables

Variables will be stored in persistence just like a linux shell, The ai owever will not access the variables.
=======
=======
>>>>>>> Stashed changes
3. **Run the Tool**:
   
   ./tool.sh  # Adjust 'tool.sh' to the name of your tool script
   
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

## Requirements
Make sure you have `ollama` installed either by snap or from the official website. You can download with `ollama pull`, a model suitable for your machine and needs and replace the `OLLAMA_MODEL` variable
## Usage

Follow the instructions provided in the documentation for how to use the tool.
<<<<<<< Updated upstream

<<<<<<< Updated upstream
```bash
git clone https://github.com/Kevinscki/llama_term.git
cd llama_term
python3 -m venv .env #create the python environment (I dont advise using --break-system-packages)
source ./.env/bin/activate
pip3 install prompt-toolkit
python3 llama_shell.py
```
You can utilize the `Modelfile` to try a slightly modified version of your model. you can then rename the model similar to the `OLLAMA_MODEL` variable in  `configuration_variables.py`.

Example:

```bash
ollama create bash_model -f Modelfile #Modelfile contains the base model to be used in creating the other model
ollama list #Your new modified model will show up
```
=======
## Contributing

Contributions are welcome! Please submit pull requests with clear descriptions of your changes.
>>>>>>> Stashed changes

## License

<<<<<<< Updated upstream
Tell the model to list files or find a file, observe the code after.
=======
=======

## Contributing

Contributions are welcome! Please submit pull requests with clear descriptions of your changes.

## License

>>>>>>> Stashed changes
This project is licensed under the MIT License. See the LICENSE file for more details.

---

Feel free to modify and expand this template as needed for your specific web_osint tool.
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
