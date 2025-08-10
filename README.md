![Deploy](https://github.com/wr1/grk/actions/workflows/tests.yml/badge.svg)![Version](https://img.shields.io/github/v/release/wr1/grk)
# grk

Use GROK API in the terminal, control input, output and profiles. 

## Features

- Prompt grok using a combination of file(s) and prompt.
- Have profiles to use different grok assistants in the same project.
- Precisely control which files go into `grok` (contrast with agents).

## Installation
<!-- With `pip`
```bash
pip install .  
```-->
Or `uv`
```bash
uv pip install https://github.com/wr1/grk.git
```

## Configuration
You can create a `.grkrc` YAML file in the current directory to set default options. It now supports multiple profiles.

```yaml
profiles:
    default:
        model: grok-4
        role: expert engineer and dev
        output: output.json
        prompt_prepend: " "
        temperature: 0.1  
    law:
        model: grok-4
        role: lawyer, expert legal scholar
        output: output.json
        prompt_prepend: ""
        temperature: 0.15
    docs:
        model: grok-4
        role: documentation-specialist
        output: output.json
        prompt_prepend: "aim for conciseness and documenting use over implementation, "
        temperature: 0.7  
brief:
    file: "design_brief.typ"
    role: "assistant"
```

## Usage

### Quick start 

Using [shorthand](resources/shorthand.fish) for fish shell. 
```shell
# write project brief
echo "write a 3d finite element solver using hex8 elements, use it to model a cube with 10x10x10 elements where x,y,z span range [0,1], clamp z==0 and apply unit distributed surface stress in positive z direction at z==1, output a vtu file where stresses and displacements are added as point data to the mesh, use numpy operations for speed and a logger to print progress to stdout, use user [{name="test",email="test@example.com"}]" > README.md

# fold the project
cf 

# start session
gu codefold.json

# ask to implement
gm "please implement according to README" -o __temp.json

# unfold and install
cu __temp.json ; uv pip install -e . 

# close session
gd

# run code
hex-fem
INFO:hex_fem.fem:Generating mesh
INFO:hex_fem.fem:Assembling stiffness
INFO:hex_fem.fem:Assembling forces
INFO:hex_fem.fem:Solving system
INFO:hex_fem.fem:Computing stresses
INFO:hex_fem.fem:Writing output
```

<!-- ![running](docs/assets/output.gif) -->
![output](docs/assets/screenshot1.png)

### Single-Shot (One-Off) Commands
```bash
grk init
grk list
grk run <input_file> <prompt> [-p <profile>]  # Note: -p is the short form for --profile
```

### Interactive (Session-Based) Commands
```bash
grk session up <initial_file> [-p <profile>]
grk session msg <prompt> [-o <output>] [-i <input_file>]
grk session list
grk session down
```

In session mode, responses are postprocessed: any explanatory messages are printed to the console, and the output file is cleaned to ensure valid JSON in {'files': [...]} format (if possible).

### Use with cfold
Chaining with [cfold](https://github.com/wr1/cfold) allows making whole codebase changes, example below using [fish shorthand](resources/shorthand.fish).
```bash
cf # fold the codebase, creates codefold.json
gu codefold.json # session up
gm "review the docs and sync with current cli" # message the session
cu __temp.json  # unfold the response 
...             # more messages
gd # close the session
```

All settings are governed by the specified profile in .grkrc. If no .grkrc exists, it uses the default profile.

## Environment Variables

- `XAI_API_KEY`: xAI API key (required)

## License 
MIT


