 # Configuration
 
 You can configure `grk` using a `.grkrc` YAML file in the current directory. This file supports multiple profiles for different use cases.
 
 ## Example `.grkrc` File
 
 ```yaml
 profiles:
   default:
     model: grok-3
     role: python-programmer
     output: output.txt
     json_out: output.json
     prompt_prepend: "Process this cfold file:\n"
   python:
     model: grok-3
     role: python-programmer
     output: output.txt
     json_out: output.json
     prompt_prepend: "Process this cfold file:\n"
   docs:
     model: grok-3
     role: documentation-specialist
     output: output.txt
     json_out: output.json
     prompt_prepend: "Process this cfold file:\n"
 ```
 
 ## Environment Variables
 
 - `XAI_API_KEY`: Required. Your xAI API key for accessing the Grok API.
 
 ## Initializing Configuration
 
 To create a default `.grkrc` file with predefined profiles, run:
 
 ```bash
 grk init
 ```
 
 If a `.grkrc` file already exists, existing profiles will be preserved with an `_old` suffix if they differ from the default profiles.
 ```
