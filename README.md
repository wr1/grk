![Deploy](https://github.com/wr1/grk/actions/workflows/tests.yml/badge.svg)![Version](https://img.shields.io/github/v/release/wr1/grk)
# grk

Use GROK API in the terminal, control input, output and profiles. 

## Features

- Prompt grok using a combination of file(s) and prompt.
- Have profiles to use different grok assistants in the same project.
- Precisely control which files go into `grok` (contrast with agents).

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
        output: output.json
        json_out: /tmp/grok_output.json
        prompt_prepend: " "
        temperature: 0.1  
    law:
        model: grok-3
        role: lawyer, expert legal scholar
        output: output.json
        json_out: output.json
        prompt_prepend: ""
        temperature: 0.15
    docs:
        model: grok-4
        role: documentation-specialist
        output: output.json
        json_out: output.json
        prompt_prepend: "aim for conciseness and documenting use over implementation, "
        temperature: 0.7  
```

## Usage

```bash
grk init
grk run <input_file> <prompt> [-p <profile>]  # Note: -p is the short form for --profile
```


### Advanced use
Chaining with [cfold](https://github.com/wr1/cfold) allows making whole codebase changes. 
```bash
# fold the local python project into a text file
cfold fold -o folded_project.json
# run instructions on the codebase
grk run folded_project.json "change the CLI framework from argparse to click"  
# unfold the changes
cfold unfold output.json
```
This can be wrapped into a shell function for convenient terminal use, for example in `fish`: 
```shell
function g 
    cfold fold -o folded_project.json
    grk run folded_project.json $argv    
    cfold unfold output.json
end
```


All settings are governed by the specified profile in .grkrc. If no .grkrc exists, it uses the default profile.

## Environment Variables

- `XAI_API_KEY`: xAI API key (required)

## License 
MIT

<!-- ## Documentation

For detailed documentation, visit our [MkDocs site](./docs/index.md) or run `mkdocs serve` locally after installing dependencies with `uv add mkdocs mkdocs-material`. -->

