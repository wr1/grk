# grk

CLI tool to push cfold files to Grok LLM and save output as cfold and JSON.

## Features

- Prompt grok using a combination of file(s) and prompt
  - Exact control over which files go into grok
- 



## Installation

```bash
uv add click requests ruamel.yaml
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
    temperature: 0  
  python:
    model: grok-3-mini-fast
    role: python-programmer
    output: output.txt
    json_out: output.json
    prompt_prepend: "Process this cfold file:\n"
    temperature: 0.15  # slightly more creative version of default
  docs:
    model: grok-3
    role: documentation-specialist
    output: output.txt
    json_out: output.json
    prompt_prepend: "Process this cfold file:\n"
    temperature: 0.7  
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
