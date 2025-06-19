"""CLI commands for interacting with Grok LLM."""

import rich_click as click  # Use rich_click for colored help and output
import json
import requests
import os
from pathlib import Path
from .config import load_config
from ruamel.yaml import YAML
import time
from rich.console import Console
from rich.syntax import Syntax
from io import StringIO

API_URL = "https://api.x.ai/v1/chat/completions"

ROLES = {
    "python-programmer": "you are an expert python programmer, writing clean code",
    "lawyer": "you are an expert lawyer, providing legal advice",
    "psychologist": "you are a professional psychologist, giving psychological advice",
    "documentation-specialist": "you are an expert in writing documentation",
}


def call_grok(
    file_content: str,
    prompt: str,
    model: str,
    api_key: str,
    system_message: str,
    temperature: float = 0,
) -> str:
    """Call Grok API with content and prompt."""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": file_content + "\n" + prompt},
        ],
        "stream": False,
        "temperature": temperature,
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
                "temperature": 0,
            },
            "py": {
                "model": "grok-3-mini-fast",
                "role": "python-programmer",
                "output": "output.txt",
                "json_out": "/tmp/grk_py_output.json",
                "prompt_prepend": "",
                "temperature": 0,
            },
            "doc": {
                "model": "grok-3",
                "role": "documentation-specialist",
                "output": "output.txt",
                "json_out": "/tmp/grk_doc_output.json",
                "prompt_prepend": "",
                "temperature": 0.7,
            },
            "law": {
                "model": "grok-3-fast",
                "role": "senior lawyer/legal scholar",
                "output": "output.txt",
                "json_out": "/tmp/grk_law_output.json",
                "prompt_prepend": "write concise legal argumentation, prefer latex, use the cenum environment for continuous numbering throughout the document. ",
                "temperature": 0.5,
            },
            "psy": {
                "model": "grok-3",
                "role": "senior psychologist",
                "output": "output.txt",
                "json_out": "/tmp/grk_psy_output.json",
                "prompt_prepend": """use standard psychological argumentation, write concise, use established psychological concepts from ICD10 and DSM5, use latex, assume cenum environment is available for continous numbering.""",
                "temperature": 0.5,
            },
        }
    }

    # Add old profiles with _old suffix only if they differ
    for profile_name, profile_data in old_profiles.items():
        if profile_name in default_config["profiles"]:
            if profile_data != default_config["profiles"][profile_name]:
                default_config["profiles"][f"{profile_name}_old"] = profile_data
                click.echo(
                    f"Profile '{profile_name}' differs from default, saved old as '{profile_name}_old'."
                )
        else:
            default_config["profiles"][f"{profile_name}_old"] = profile_data
            click.echo(
                f"Profile '{profile_name}' not in default config, saved as '{profile_name}_old'."
            )

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
@click.option("-p", "--profile", default="default", help="The profile to use")
def run(file: str, prompt: str, profile: str = "default"):
    """Run the Grok LLM processing using the specified profile."""
    config = load_config(profile)  # Returns ProfileConfig object
    model_used = config.model or "grok-3-mini-fast"
    role_from_config = config.role or "python-programmer"
    output_file = config.output or "output.txt"
    json_out_file = config.json_out or "output.json"
    prompt_prepend = config.prompt_prepend or ""
    temperature = config.temperature or 0

    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise click.ClickException(
            "API key is required via XAI_API_KEY environment variable."
        )

    try:
        file_content = Path(file).read_text()
    except Exception as e:
        raise click.ClickException(f"Failed to read file: {str(e)}")

    system_message = ROLES.get(role_from_config, ROLES["python-programmer"])
    full_prompt = prompt_prepend + prompt

    console = Console()
    console.print("[bold green]Running grk[/bold green] with the following settings:")
    console.print(f"  Profile: [cyan]{profile}[/cyan]")
    console.print(f"  Model: [yellow]{model_used}[/yellow]")
    console.print(f"  Role: [cyan]{role_from_config}[/cyan]")
    console.print(f"  File: [cyan]{file}[/cyan]")
    console.print(f"  Prompt: [italic green]{full_prompt}[/italic green]")
    console.print(f"  Temperature: [red]{temperature}[/red]")

    with console.status("[bold green]Calling Grok API...[/bold green]"):
        start_time = time.time()
        response = call_grok(
            file_content, full_prompt, model_used, api_key, system_message, temperature
        )
        end_time = time.time()
        wait_time = end_time - start_time
    click.echo(f"API call completed in {wait_time:.2f} seconds.")

    try:
        Path(output_file).write_text(response)
        with Path(json_out_file).open("w") as f:
            json.dump(
                {
                    "input": file_content,
                    "prompt": full_prompt,
                    "response": response,
                    "used_role": role_from_config,
                    "used_profile": profile,
                },
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
            with StringIO() as stream:
                yaml_dumper.dump({"profiles": profiles}, stream)
                yaml_str = stream.getvalue()
            syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=True)
            console = Console()
            console.print(syntax)
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
