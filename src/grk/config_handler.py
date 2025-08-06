"""Handlers for configuration file operations."""

from pathlib import Path
from ruamel.yaml import YAML
from io import StringIO
from rich.console import Console
from rich.syntax import Syntax
import click


def list_configs():
    """List configurations from .grkrc with YAML syntax highlighting."""
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



