 # grk
 
 CLI tool to push cfold files to Grok LLM and save output as cfold and JSON.
 
 ## Installation
 
 ```bash
 uv pip install . 
 ```
 
 ## Configuration
 
 You can create a `.grkrc` YAML file in the current directory to set default options. It now supports multiple profiles.
 
 ```yaml
 profiles:
   default:
     model: grok-3-mini-fast
     role: python-programmer
     output: output.txt
     json_out: /tmp/grk_default_output.json
     prompt_prepend: "Process this cfold file:\n"
     temperature: 0  # New option for API temperature
   python:
     model: grok-3-mini-fast
     role: python-programmer
     output: output.txt
     json_out: /tmp/grk_python_output.json
     prompt_prepend: "Process this cfold file:\n"
     temperature: 0  # New option for API temperature
   docs:
     model: grok-3
     role: documentation-specialist
     output: output.txt
     json_out: /tmp/grk_docs_output.json
     prompt_prepend: "Process this cfold file:\n"
     temperature: 0.7  # New option for API temperature
 ```
 
 ## Usage
 
 ```bash
 grk init
 grk run <input_file> <prompt> [-p <profile>]
 ```
 
 For example:

 ```bash
 grk run input.txt "Process the instructions in this text file" -p python
 ```

All settings are governed by the specified profile in .grkrc. If no .grkrc exists, it uses the default profile.
 
### Advanced use
Chaining with [cfold](https://github.com/wr1/cfold) allows making whole codebase changes. 
 ```bash
 # fold the local python project into a text file
 cfold fold -o folded_project.txt
 # run instructions on the codebase
 grk run folded_project.txt "change the CLI framework from argparse to click"  
 # unfold the changes
 cfold unfold output.txt
 ```
This can be wrapped into a shell function for convenient terminal use, for example in `fish`: 
```fish 
function g 
  cfold fold -o folded_project.txt
  grk run folded_project.txt $argv  
  cfold unfold output.txt
end
```

 ## Environment Variables
 
 - `XAI_API_KEY`: xAI API key (required)
 
 ## Documentation
 
 For detailed documentation, visit our [MkDocs site](./docs/index.md) or run `mkdocs serve` locally after installing dependencies with `uv add mkdocs mkdocs-material`.

