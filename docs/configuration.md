# Configuration

You can configure `grk` using a `.grkrc` YAML file in the current directory. This file supports multiple profiles for different use cases.

## Example `.grkrc` File

```yaml
profiles:
  default:
    model: grok-4
    role: python-programmer
    output: output.json
    json_out: /tmp/grk_default_output.json
    prompt_prepend: ""
    temperature: 0  
  py:
    model: grok-3-mini-fast
    role: python-programmer
    output: output.json
    json_out: /tmp/grk_py_output.json
    prompt_prepend: ""
    temperature: 0 
  doc:
    model: grok-3
    role: documentation-specialist
    output: output.json
    json_out: /tmp/grk_doc_output.json
    prompt_prepend: ""
    temperature: 0.7 
  law:
    model: grok-4
    role: senior lawyer/legal scholar
    output: output.json
    json_out: /tmp/grk_law_output.json
    prompt_prepend: "write concise legal argumentation, prefer latex, use the cenum environment for continuous numbering throughout the document. "
    temperature: 0.5  
```

## Environment Variables

- `XAI_API_KEY`: Required. Your xAI API key for accessing the Grok API.

## Initializing Configuration

To create a default `.grkrc` file with predefined profiles, run:

```bash
grk init
```

If a `.grkrc` file already exists, existing profiles will be preserved with an `_old` suffix if they differ from the default profiles.


