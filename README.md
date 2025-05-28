 # grk
 
 CLI tool to push cfold files to Grok LLM and save output as cfold and JSON.
 
 ## Installation
 
 ```bash
 poetry install
 ```
 
 ## Usage
 
 ```bash
 grk input.txt -p "Process this cfold" -o output.txt -j full.json -m grok-3 -k your_api_key
 ```
 
 ## Environment Variables
 
 - `XAI_API_KEY`: xAI API key (required)
