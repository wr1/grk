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
grk session up <initial_file> [-p <profile>]
grk session q <prompt> [-o <output>] [-i <input_file>] [-l]  # -l to list session details
grk session down
```

### Examples

Run with a specific profile and input file (single-shot):

```bash
grk run input.txt "Process this text file" -p py
```

Start an interactive session and query it:

```bash
grk session up initial.json -p default
grk session q "Update the code" -o updated.json
grk session q -l  # List session details
grk session down
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
grk session --help  # For session-specific help
```


