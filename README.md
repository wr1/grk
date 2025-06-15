 # grk
 
 CLI tool to push cfold files to Grok LLM and save output as cfold and JSON.
 
 ## Installation
 
 ```bash
 poetry install
 ```
 
 ### Fish Shell Completions
 
 To enable command-line completions for `grk` in Fish shell:
 
 ```bash
 mkdir -p ~/.config/fish/completions
 cp completions/grk.fish ~/.config/fish/completions/
 ```
 
 ## Configuration
 
 You can create a `.grkrc` YAML file in the current directory to set default options:
 
 ```yaml
 model: grok-3
 role: python-programmer
 output: output.txt
 json_out: output.json
 prompt_prepend: "Process this cfold file:\n"
 ```
 
 Command-line options override `.grkrc` values.
 
 ## Usage
 
 ```bash
 grk init
 grk run input.txt "Process this cfold" -o output.txt -j full.json -m grok-3 -k your_api_key -r python-programmer
 ```
 
 ### Options
 
 These options apply to the `grk run` subcommand:
 - `-o/--output`: Specify output file (default: `output.txt` or `.grkrc` value)
 - `-j/--json-out`: Specify JSON output file (default: `output.json` or `.grkrc` value)
 - `-m/--model`: Grok model (default: `grok-3-mini` or `.grkrc` value)
 - `-k/--api-key`: xAI API key (or set `XAI_API_KEY` env var)
 - `-r/--role`: System role (default: `python-programmer` or `.grkrc` value; options: `python-programmer`, `lawyer`, `psychologist`)
 
 ## Environment Variables
 
 - `XAI_API_KEY`: xAI API key (required)
