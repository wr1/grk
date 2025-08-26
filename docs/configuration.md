# Configuration

You can configure `grk` using a `.grkrc` YAML file in the current directory. This file supports multiple profiles for different use cases.

## Example `.grkrc` File

```yaml
profiles:
    default:
        model: grok-4
        role: you are an expert engineer and developer
        output: output.json
        prompt_prepend: ""
        temperature: 0.25
    py:
        model: grok-4
        role: you are an expert python programmer, writing clean code
        output: output.json
        prompt_prepend: ""
        temperature: 0
    doc:
        model: grok-4
        role: you are an expert in writing documentation
        output: output.json
        prompt_prepend: ""
        temperature: 0.7
    law:
        model: grok-4
        role: you are an expert lawyer, providing legal advice
        output: output.json
        prompt_prepend: write concise legal argumentation, prefer latex
        temperature: 0.35
    psy:
        model: grok-4
        role: you are an expert professor in psychology
        output: output.json
        prompt_prepend: ""
        temperature: 0.3
brief:
    file: "design_brief.typ"
    role: "assistant"
```

## Environment Variables

- `XAI_API_KEY`: Required. Your xAI API key for accessing the Grok API.

## Initializing Configuration

To create a default `.grkrc` file with predefined profiles, run:

```bash
grk init
```

If a `.grkrc` file already exists, existing profiles will be preserved with an `_old` suffix if they differ from the default profiles.






