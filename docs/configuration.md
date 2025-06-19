 # Configuration
 
 You can configure `grk` using a `.grkrc` YAML file in the current directory. This file supports multiple profiles for different use cases.
 
 ## Example `.grkrc` File
 
 ```yaml
 profiles:
   default:
     model: grok-3-mini-fast
     role: python-programmer
     output: output.txt
     json_out: /tmp/grk_default_output.json
     prompt_prepend: ""
     temperature: 0  # New option for API temperature
   py:
     model: grok-3-mini-fast
     role: python-programmer
     output: output.txt
     json_out: /tmp/grk_py_output.json
     prompt_prepend: ""
     temperature: 0  # New option for API temperature
   doc:
     model: grok-3
     role: documentation-specialist
     output: output.txt
     json_out: /tmp/grk_doc_output.json
     prompt_prepend: ""
     temperature: 0.7  # New option for API temperature
   law:
     model: grok-3-fast
     role: senior lawyer/legal scholar
     output: output.txt
     json_out: /tmp/grk_law_output.json
     prompt_prepend: "write concise legal argumentation, prefer latex, use the cenum environment for continuous numbering throughout the document. "
     temperature: 0.5  # New option for API temperature
   psy:
     model: grok-3
     role: senior psychologist
     output: output.txt
     json_out: /tmp/grk_psy_output.json
     prompt_prepend: "use standard psychological argumentation, write concise, use established psychological concepts from ICD10 and DSM5, use latex, assume cenum environment is available for continuous numbering."
     temperature: 0.5  # New option for API temperature
 ```
 
 ## Environment Variables
 
 - `XAI_API_KEY`: Required. Your xAI API key for accessing the Grok API.
 
 ## Initializing Configuration
 
 To create a default `.grkrc` file with predefined profiles, run:
 
 ```bash
 grk init
 ```
 
 If a `.grkrc` file already exists, existing profiles will be preserved with an `_old` suffix if they differ from the default profiles.
