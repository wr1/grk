 # grk
 
 CLI tool to push cfold files to Grok LLM and save output as cfold and JSON.
 
 ## Installation
 
 ```bash
 uv add click requests ruamel.yaml
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
     model: grok-3-mini-fast
     role: python-programmer
     output: output.txt
     json_out: output.json
     prompt_prepend: "Process this cfold file:\n"
     temperature: 0  # New option for API temperature
   python:
     model: grok-3-mini-fast
     role: python-programmer
     output: output.txt
     json_out: output.json
     prompt_prepend: "Process this cfold file:\n"
     temperature: 0  # New option for API temperature
   docs:
     model: grok-3
     role: documentation-specialist
     output: output.txt
     json_out: output.json
     prompt_prepend: "Process this cfold file:\n"
     temperature: 0.7  # New option for API temperature
 ```
 
 ## Usage
 
 ```bash
 grk init
 grk run <input_file> <prompt> [-p <profile>]
 ```
 
 For example:
 grk run input.txt "Process this cfold" -p python
 
 All settings are governed by the specified profile in .grkrc. If no .grkrc exists, it uses the default profile.
 
 ## Environment Variables
 
 - `XAI_API_KEY`: xAI API key (required)
 
 ## Documentation
 
 For detailed documentation, visit our [MkDocs site](./docs/index.md) or run `mkdocs serve` locally after installing dependencies with `uv add mkdocs mkdocs-material`.

