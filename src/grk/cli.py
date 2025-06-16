import click
import os
from pathlib import Path
from .config import create_default_config, load_config
from .api import call_grok  # Import the API utility
import time
from rich.console import Console

API_URL = "https://api.x.ai/v1/chat/completions"

# Predefined roles with their system messages
ROLES = {
    "python-programmer": "you are an expert python programmer, writing clean code",
    "lawyer": "you are an expert lawyer, providing legal advice",
    "psychologist": "you are a professional psychologist, giving psychological advice",
    "documentation-specialist": "you are an expert in writing documentation",
}

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
    config = load_config(profile)
    output_file = config.get("output", "output.txt")
    json_out_file = config.get("json_out", "output.json")
    model_used = config.get("model", "grok-3-mini-fast")
    role_from_config = config.get("role", "python-programmer")
    role_used = role_from_config
    prompt_prepend = config.get("prompt_prepend", "")
    temperature = config.get("temperature", 0)

    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise click.ClickException("API key is required via XAI_API_KEY environment variable.")

    try:
        file_content = Path(file).read_text()
    except Exception as e:
        raise click.ClickException(f"Failed to read file: {str(e)}")

    system_message = ROLES.get(role_used, ROLES["python-programmer"])
    full_prompt = prompt_prepend + prompt

    console = Console()
    console.print("[bold green]Running grk[/bold green] with the following settings:")
    console.print(f"  Profile: [bold blue]{profile}[/bold blue]")
    console.print(f"  Model: [yellow]{model_used}[/yellow]")
    console.print(f"  Role: [purple]{role_used}[/purple]")
    console.print(f"  File: [cyan]{file}[/cyan]")
    console.print(f"  Prompt: [italic]{full_prompt}[/italic]")
    console.print(f"  Temperature: [red]{temperature}[/red]")

    with console.status("[bold green]Calling Grok API...[/bold green]"):
        start_time = time.time()
        response = call_grok(file_content, full_prompt, model_used, api_key, system_message, temperature)
        end_time = time.time()
        wait_time = end_time - start_time
    click.echo(f"API call completed in {wait_time:.2f} seconds.")

    try:
        Path(output_file).write_text(response)
        with Path(json_out_file).open("w") as f:
            import json
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
        from ruamel.yaml import YAML
        yaml = YAML()
        with config_file.open("r") as f:
            full_config = yaml.load(f) or {}
        profiles = full_config.get("profiles", {})
        if profiles:
            yaml_dumper = YAML()
            from io import StringIO
            from rich.syntax import Syntax
            from rich.console import Console
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
