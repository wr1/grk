import click
import json
import requests
from pathlib import Path
import yaml
from .config import load_config

API_URL = "https://api.x.ai/v1/chat/completions"

# Predefined roles with their system messages
ROLES = {
    "python-programmer": "you are an expert python programmer, writing clean code",
    "lawyer": "you are an expert lawyer, providing legal advice",
    "psychologist": "you are a professional psychologist, giving psychological advice",
}

def call_grok(file_content: str, prompt: str, model: str, api_key: str, system_message: str) -> str:
    """Call Grok API with content and prompt."""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": file_content + "\n" + prompt},
        ],
    }
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.RequestException as e:
        raise click.ClickException(f"API request failed: {str(e)}")

def create_default_config():
    """Create default .grkrc file with normal defaults."""
    default_config = {
        "model": "grok-3",
        "role": "python-programmer",
        "output": "output.txt",
        "json_out": "output.json",
        "prompt_prepend": "Process this cfold file:\n"
    }
    try:
        with open(".grkrc", "w") as f:
            yaml.dump(default_config, f)
        click.echo("Default .grkrc created successfully.")
    except Exception as e:
        click.echo(f"Failed to create .grkrc: {str(e)}")

@click.group()
def main():
    """CLI tool to interact with Grok LLM."""
    pass

@main.command()
def init():
    """Initialize .grkrc with defaults."""
    create_default_config()

@main.command()
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@click.argument("prompt")
@click.option("-o", "--output", help="Output file for response")
@click.option("-j", "--json-out", help="Output JSON file")
@click.option("-m", "--model", help="Grok model to use")
@click.option("-k", "--api-key", required=True, envvar="XAI_API_KEY", help="xAI API key")
@click.option("-r", "--role", type=click.Choice(ROLES.keys(), case_sensitive=False), help="System role")
def run(file: str, prompt: str, output: str, json_out: str, model: str, api_key: str, role: str):
    """Run the Grok LLM processing."""
    config = load_config()
    output = output or config.get("output", "output.txt")
    json_out = json_out or config.get("json_out", "output.json")  # Updated from /tmp/ for better practice
    model = model or config.get("model", "grok-3-mini-fast")
    role = role or config.get("role", "python-programmer")
    prompt_prepend = config.get("prompt_prepend", "")
    try:
        file_content = Path(file).read_text()
    except Exception as e:
        raise click.ClickException(f"Failed to read file: {str(e)}")
    system_message = ROLES.get(role, ROLES["python-programmer"])
    full_prompt = prompt_prepend + prompt
    click.echo(f"Running grk with model {model} on file {file} and prompt {full_prompt}")
    response = call_grok(file_content, full_prompt, model, api_key, system_message)
    try:
        Path(output).write_text(response)
        with Path(json_out).open("w") as f:
            json.dump(
                {"input": file_content, "prompt": full_prompt, "response": response, "used_role": role},
                f,
                indent=2,
            )
        click.echo(f"Response saved to {output} and {json_out}")
    except Exception as e:
        raise click.ClickException(f"Failed to write output: {str(e)}")

if __name__ == "__main__":
    main()
