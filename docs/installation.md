# Installation

To install `grk`, we recommend using `uv` for dependency management. Follow these steps:

```bash
uv add click requests ruamel.yaml rich
```

If you are a developer and want to work on `grk` or build documentation locally, you can install additional dependencies:

```bash
uv add mkdocs mkdocs-material pytest pytest-mock pyinstaller
```

### Fish Shell Completions

To enable command-line completions for `grk` in Fish shell:

```bash
mkdir -p ~/.config/fish/completions
cp completions/grk.fish ~/.config/fish/completions/
```
