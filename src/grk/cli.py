import click
import json
import requests
import os
from pathlib import Path
from .config import load_config
from ruamel.yaml import YAML
import time  # Added for timing the API call
from rich.console import Console  # Added for terminal visualization
from rich.syntax import Syntax  # Added for YAML syntax highlighting
from io import StringIO  # Added for dumping YAML to string

API_URL = "https://api.x.ai/v1/chat/completions"

# Predefined roles with their system messages
ROLES = {
    "python-programmer": "you are an expert python programmer, writing clean code",
    "lawyer": "you are an expert lawyer, providing legal advice",
    "psychologist": "you are a professional psychologist, giving psychological advice",
    "documentation-specialist": "you are an expert in writing documentation",
}

def call_grok(file_content: str, prompt: str, model: str, api_key: str, system_message: str, temperature: float = 0) -> str:
    """Call Grok API with content and prompt."""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": file_content + "\n" + prompt},
        ],
        "stream": False,
        "temperature": temperature,  # Use provided temperature
    }
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.RequestException as e:
        raise click.ClickException(f"API request failed: {str(e)}")

def create_default_config():
    """Create default .grkrc file with profiles, preserving old profiles with _old suffix if different."""
    config_file = Path(".grkrc")
    old_profiles = {}
    if config_file.exists():
        try:
            yaml = YAML()
            with config_file.open("r") as f:
                existing_config = yaml.load(f) or {}
            old_profiles = existing_config.get("profiles", {})
        except Exception as e:
            click.echo(f"Warning: Failed to load existing .grkrc: {str(e)}")

    default_config = {
        "profiles": {
            "default": {
                "model": "grok-3-mini-fast",
                "role": "python-programmer",
                "output": "output.txt",
                "json_out": "/tmp/grk_default_output.json",
                "prompt_prepend": "",
                "temperature": 0  # Added temperature option
            },
            "py": {
                "model": "grok-3-mini-fast",
                "role": "python-programmer",
                "output": "output.txt",
                "json_out": "/tmp/grk_py_output.json",
                "prompt_prepend": "",
                "temperature": 0  # Added temperature option
            },
            "doc": {
                "model": "grok-3",
                "role": "documentation-specialist",
                "output": "output.txt",
                "json_out": "/tmp/grk_doc_output.json",
                "prompt_prepend": "",
                "temperature": 0.7  # Added temperature option
            },
            "law": {
                "model": "grok-3-fast",
                "role": "senior lawyer/legal scholar",
                "output": "output.txt",
                "json_out": "/tmp/grk_law_output.json",
                "prompt_prepend": "write concise legal argumentation, prefer latex, use the cenum environment for continuous numbering throughout the document. ",
                "temperature": 0.5  # Added temperature option
            },
            "psy": {
                "model": "grok-3",
                "role": "senior psychologist",
                "output": "output.txt",
                "json_out": "/tmp/grk_psy_output.json",
                "prompt_prepend": """use standard psychological argumentation, write concise, use established psychological concepts from ICD10 and DSM5, use latex, assume cenum environment is available for continous numbering.""",
                "temperature": 0.5  # Added temperature option
            },
        }
    }

    # Add old profiles with _old suffix only if they differ from the new ones
    for profile_name, profile_data in old_profiles.items():
        if profile_name in default_config["profiles"]:
            if profile_data != default_config["profiles"][profile_name]:
                default_config["profiles"][f"{profile_name}_old"] = profile_data
                click.echo(f"Profile '{profile_name}' differs from default, saved old as '{profile_name}_old'.")
        else:
            default_config["profiles"][f"{profile_name}_old"] = profile_data
            click.echo(f"Profile '{profile_name}' not in default config, saved as '{profile_name}_old'.")

    try:
        yaml = YAML()
        with open(".grkrc", "w") as f:
            yaml.dump(default_config, f)
        click.echo("Default .grkrc with profiles created successfully.")
    except Exception as e:
        click.echo(f"Failed to create .grkrc: {str(e)}")

@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def main():
    """CLI tool to interact with Grok LLM."""
    pass

@main.command()
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@click.argument("prompt")
@click.option("-p", "--profile", default="default", help="The profile to use (e.g., default, py, doc, law, psy)")
def run(file: str, prompt: str, profile: str = "default"):
    """Run the Grok LLM processing using the specified profile."""
    config = load_config(profile)  # Load config; if no .grkrc, returns {}
    output_file = config.get("output", "output.txt")  # Use config or default
    json_out_file = config.get("json_out", "output.json")
    model_used = config.get("model", "grok-3-mini-fast")
    role_from_config = config.get("role", "python-programmer")
    role_used = role_from_config  # Use role from config only
    prompt_prepend = config.get("prompt_prepend", "")
    temperature = config.get("temperature", 0)  # Added temperature from config

    # API key must be from environment variable
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise click.ClickException("API key is required via XAI_API_KEY environment variable.")

    try:
        file_content = Path(file).read_text()
    except Exception as e:
        raise click.ClickException(f"Failed to read file: {str(e)}")

    system_message = ROLES.get(role_used, ROLES["python-programmer"])
    full_prompt = prompt_prepend + prompt

    console = Console()  # Initialize rich console for visualization
    # Rich formatted message for profile parameters, file, and prompt, now multiline
    console.print("[bold green]Running grk[/bold green] with the following settings:")
    console.print(f"  Profile: [bold blue]{profile}[/bold blue]")
    console.print(f"  Model: [yellow]{model_used}[/yellow]")
    console.print(f"  Role: [purple]{role_used}[/purple]")
    console.print(f"  File: [cyan]{file}[/cyan]")
    console.print(f"  Prompt: [italic]{full_prompt}[/italic]")
    console.print(f"  Temperature: [red]{temperature}[/red]")

    with console.status("[bold green]Calling Grok API...[/bold green]"):  # Show spinner during API call
        start_time = time.time()  # Record start time for API call
        response = call_grok(file_content, full_prompt, model_used, api_key, system_message, temperature)
        end_time = time.time()  # Record end time
        wait_time = end_time - start_time  # Calculate wait time
    click.echo(f"API call completed in {wait_time:.2f} seconds.")  # Print wait time

    try:
        Path(output_file).write_text(response)
        with Path(json_out_file).open("w") as f:
            json.dump(
                {"input": file_content, "prompt": full_prompt, "response": response, "used_role": role_used, "used_profile": profile},
                f,
                indent=2,
            )
        click.echo(f"Response saved to {output_file} and {json_out_file}")
    except Exception as e:
        raise click.ClickException(f"Failed to write output: {str(e)}")

@main.command()
def list():
    """List the configurations from .grkrc with YAML syntax highlighting."""
    config_file = Path(".grkrc")
    if not config_file.exists():
        click.echo("No .grkrc file found in the current directory.")
        return
    try:
        yaml = YAML()
        with config_file.open("r") as f:
            full_config = yaml.load(f) or {}
        profiles = full_config.get("profiles", {})
        if profiles:
            yaml_dumper = YAML()
            with StringIO() as stream:  # Use StringIO to get YAML as string
                yaml_dumper.dump({"profiles": profiles}, stream)
                yaml_str = stream.getvalue()
            syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=True)  # Highlight YAML
            console = Console()
            console.print(syntax)  # Display with highlighting
        else:
            click.echo("No profiles defined in .grkrc.")
    except Exception as e:
        click.echo(f"Warning: Failed to load .grkrc: {str(e)}")

@main.command()
def init():
    """Initialize .grkrc with default profiles."""
    create_default_config()

if __name__ == "__main__":
    main()
