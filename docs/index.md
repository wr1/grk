# Welcome to grk

`grk` is a command-line interface (CLI) tool designed to interact with the Grok LLM API. It allows users to push cfold files to Grok LLM and save the output in both cfold and JSON formats.

## Key Features

- **Profile-based Configuration**: Manage multiple configurations for different use cases with a `.grkrc` file.
- **Flexible Input/Output**: Process input files and save responses as JSON and text.
- **Role-based System Messages**: Choose predefined roles for Grok (e.g., Python programmer, lawyer) to tailor responses.
- **Terminal Visualization**: Enhanced user experience with rich terminal output for better readability.

## Design considerations
- **No magic**: Control what gets sent to the LLM by explicitly *folding* the files into a single text file, avoid background reading of git histories etc. 
- **Enable legal applications**: For use with legal documents, it is important that e.g. only pseudonymized versions of documents get submitted. 

## Getting Started

- [Installation](./installation.md)
- [Usage Guide](./usage.md)
- [Configuration](./configuration.md)

