# Configuration

You can configure `grk` using a `.grkrc` YAML file in the current directory. This file supports multiple profiles for different use cases.

## Example `.grkrc` File

```yaml
profiles:
  default:
    model: grok4
    role: python-programmer
    output: output.json
    prompt_prepend: ""
    temperature: 0  
  py:
    model: grok4
    role: python-programmer
    output: output.json
    prompt_prepend: ""
    temperature: 0 
  doc:
    model: grok4
    role: documentation-specialist
    output: output.json
    prompt_prepend: ""
    temperature: 0.7 
  law:
    model: grok4
    role: senior lawyer/legal scholar
    output: output.json
    prompt_prepend: "write concise legal argumentation, prefer latex, use the cenum environment for continuous numbering throughout the document. "
    temperature: 0.5  
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





