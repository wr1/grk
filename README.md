![Deploy](https://github.com/wr1/grk/actions/workflows/tests.yml/badge.svg)![Version](https://img.shields.io/github/v/release/wr1/grk)
# grk

CLI tool to push cfold files to Grok LLM and save output as cfold and JSON.

## Features

- Prompt grok using a combination of file(s) and prompt
- Exact control over which files go into grok


## Installation
With `pip`
```bash
pip install . 
```
Or `uv`
```bash
uv pip install . 
```


## Configuration

You can create a `.grkrc` YAML file in the current directory to set default options. It now supports multiple profiles.

```yaml
profiles:
    default:
        model: grok-4
        role: expert engineer and dev
        output: output.txt
        json_out: /tmp/grok_output.json
        prompt_prepend: " "
        temperature: 0.1  
    python:
        model: grok-3-mini-fast
        role: python-programmer
        output: output.txt
        json_out: output.json
        prompt_prepend: ""
        temperature: 0.15
    docs:
        model: grok-4
        role: documentation-specialist
        output: output.txt
        json_out: output.json
        prompt_prepend: "aim for conciseness and documenting use over implementation, "
        temperature: 0.7  
```

## Usage

```bash
grk init
grk run <input_file> <prompt> [-p <profile>]
```


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
```shell
function g 
    cfold fold -o folded_project.txt
    grk run folded_project.txt $argv    
    cfold unfold output.txt
end
```


All settings are governed by the specified profile in .grkrc. If no .grkrc exists, it uses the default profile.

## Environment Variables

- `XAI_API_KEY`: xAI API key (required)

<!-- ## Documentation

For detailed documentation, visit our [MkDocs site](./docs/index.md) or run `mkdocs serve` locally after installing dependencies with `uv add mkdocs mkdocs-material`. -->
