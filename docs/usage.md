# Usage

The `grk` CLI provides commands to initialize configuration, list profiles, and run Grok LLM processing on input files.

## Basic Commands

```bash
grk init 
grk list
grk run <input_file> <prompt> [-p <profile>]  # Note: -p is the short form for --profile
```

### Examples

Run with a specific profile and input file:

```bash
grk run input.txt "Process this text file" -p py
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

