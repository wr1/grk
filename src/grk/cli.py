"""CLI commands for interacting with Grok LLM."""

import rich_click as click  # Use rich_click for colored help and output
import json
import os
from pathlib import Path
from .config import load_config, create_default_config
from .api import call_grok
from ruamel.yaml import YAML
import time
from rich.console import Console
from rich.syntax import Syntax
from io import StringIO
from concurrent.futures import ThreadPoolExecutor
from rich.live import Live
from rich.spinner import Spinner

@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def main():
    """CLI tool to interact with Grok LLM."""
    pass

@main.command()
@click.option("-f", "--file", type=click.Path(exists=True, dir_okay=False), required=True, help="Input file path")
@click.option("--prompt", required=True, help="Prompt for the LLM")
@click.option("-p", "--profile", default="default", help="The profile to use")
def run(file: str, prompt: str, profile: str = "default"):
    """Run the Grok LLM processing using the specified profile."""
    config = load_config(profile)  # Returns ProfileConfig object
    model_used = config.model or "grok-3-mini-fast"
    role_from_config = config.role or "you are an expert python programmer, writing clean code"
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

    full_prompt = prompt_prepend + prompt

    console = Console()
    console.print("[bold green]Running grk[/bold green] with the following settings:")
    console.print(f"  Profile: [cyan]{profile}[/cyan]")
    console.print(f"  Model: [yellow]{model_used}[/yellow]")
    console.print(f"  Role: [cyan]{role_from_config}[/cyan]")
    console.print(f"  File: [cyan]{file}[/cyan]")
    console.print(f"  Prompt: [italic green]{full_prompt}[/italic green]")
    console.print(f"  Temperature: [red]{temperature}[/red]")

    console.print("[bold green]Calling Grok API...[/bold green]")
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(
            call_grok,
            file_content,
            full_prompt,
            model_used,
            api_key,
            role_from_config,
            temperature,
        )
        spinner = Spinner("dots", "Waiting for API response...")
        with Live(spinner, console=console, refresh_per_second=10, transient=True):
            while not future.done():
                time.sleep(0.1)
        response = future.result()

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
