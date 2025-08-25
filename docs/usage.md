# Usage

The `grk` CLI provides commands to initialize configuration, list profiles, and run Grok LLM processing on input files. Commands are grouped into single-shot (one-off) and interactive (session-based) modes.

## Single-Shot Commands

```bash
grk config init 
grk config list
grk single run <input_file> <prompt> [-p <profile>]  # Note: -p is the short form for --profile
```

## Interactive (Session-Based) Commands

Start a background session, query it multiple times, list details, and shut it down:

```bash
grk session up <initial_file> [-p <profile>]  # Note: -p is the short form for --profile
grk session new <file.json>  # Renew instruction stack with new file
grk session msg <prompt> [-o <output>] [-i <input_file>]  # Note: -o is short for --output, -i is short for --input
grk session list  # List session details
grk session down
```

In session mode, responses are automatically postprocessed: explanatory messages are printed to the console, and the output file is cleaned to valid JSON (e.g., {'files': [...]}) if possible.

### Examples

Run with a specific profile and input file (single-shot):

```bash
grk single run input.txt "Process this text file" -p py
```

Start an interactive session, query it, list details, and shut down:

```bash
grk session up initial.json -p default
grk session msg "Update the code" -o updated.json
grk session list  # List session details
grk session down
```

List available profiles with syntax highlighting:

```bash
grk config list
```

Get help:

```bash
grk -h
# or
grk --help
grk session --help  # For session-specific help
```







