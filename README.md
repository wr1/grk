 # grk
 
 CLI tool to push cfold files to Grok LLM and save output as cfold and JSON.
 
 ## Installation
 
 ```bash
 uv add click requests pyyaml  # Use uv for installation
 ```
 
 ### Fish Shell Completions
 
 To enable command-line completions for `grk` in Fish shell:
 
 ```bash
 mkdir -p ~/.config/fish/completions
 cp completions/grk.fish ~/.config/fish/completions/
 ```
 
 ## Configuration
 
 You can create a `.grkrc` YAML file in the current directory to set default options. It now supports multiple profiles.
 
 ```yaml
 profiles:
   default:
     model: grok-3
     role: python-programmer
     output: output.txt
     json_out: output.json
     prompt_prepend: "Process this cfold file:\n"
   python:
     model: grok-3
     role: python-programmer
     output: output.txt
     json_out: output.json
     prompt_prepend: "Process this cfold file:\n"
   docs:
     model: grok-3
     role: documentation-specialist
     output: output.txt
     json_out: output.json
     prompt_prepend: "Process this cfold file:\n"
 ```
 
 Command-line options override profile values.
 
 ## Usage
 
 ```bash
 grk init
 grk run input.txt "Process this cfold" -o output.txt -j full.json -m grok-3 -k your_api_key -r python-programmer -p python
 ```
 
 ### Options
 
 These options apply to the `grk run` subcommand:
 - `-o/--output`: Specify output file (default: profile value or `output.txt`)
 - `-j/--json-out`: Specify JSON output file (default: profile value or `output.json`)
 - `-m/--model`: Grok model (default: profile value or `grok-3-mini-fast`)
 - `-k/--api-key`: xAI API key (or set `XAI_API_KEY` env var)
 - `-r/--role`: System role (overrides profile role; e.g., `python-programmer`)
 - `-p/--profile`: Profile to use (e.g., `default`, `python`, `docs`; default: `default`)
 
 ## Environment Variables
 
 - `XAI_API_KEY`: xAI API key (required)
