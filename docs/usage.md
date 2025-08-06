# Usage

The `grk` CLI provides commands to initialize configuration, list profiles, and run Grok LLM processing on input files. Commands are grouped into single-shot (one-off) and interactive (session-based) modes.

## Single-Shot Commands

```bash
grk init 
grk list
grk run <input_file> <prompt> [-p <profile>]  # Note: -p is the short form for --profile
```

## Interactive (Session-Based) Commands

Start a background session, query it multiple times, and shut it down:

```bash
grk up <initial_file> [-p <profile>]
grk q <prompt> [-o <output>] [-i <input_file>] [-l]  # -l to list session details
grk down
```

In session mode, responses are automatically postprocessed: explanatory messages are printed to the console, and the output file is cleaned to valid JSON (e.g., {'files': [...]}) if possible.

### Examples

Run with a specific profile and input file (single-shot):

```bash
grk run input.txt "Process this text file" -p py
```

Start an interactive session and query it:

```bash
grk up initial.json -p default
grk q "Update the code" -o updated.json
grk q -l  # List session details
grk down
```

List available profiles with syntax highlighting:

```bash
grk list
```

Get help:

```bash
grk -h
# or
grk --help
```



