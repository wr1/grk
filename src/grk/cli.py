"""CLI commands for interacting with Grok LLM."""

import rich_click as click
import os
from .config import load_config, create_default_config
from .runner import run_grok
from .config_handler import list_configs


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def main():
    """CLI tool to interact with Grok LLM."""
    pass


@main.command()
@click.argument("file", type=click.Path(exists=True, dir_okay=False), required=True)
@click.argument("message", required=True)
@click.option("-p", "--profile", default="default", help="The profile to use")
def run(file: str, message: str, profile: str = "default"):
    """Run the Grok LLM processing using the specified profile."""
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise click.ClickException(
            "API key is required via XAI_API_KEY environment variable."
        )
    config = load_config(profile)
    run_grok(file, message, config, api_key)


@main.command()
def list():
    """List the configurations from .grkrc with YAML syntax highlighting."""
    list_configs()


@main.command()
def init():
    """Initialize .grkrc with default profiles."""
    create_default_config()


if __name__ == "__main__":
    main()

