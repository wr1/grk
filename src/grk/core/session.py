"""Core logic for managing interactive sessions and caching."""

import json
from typing import List, Union
from pathlib import Path
import click
from rich.console import Console
from ..api import call_grok  # Import API call
from ..models import ProfileConfig
# from ..utils import analyze_changes, load_cached_codebase, save_cached_codebase
from xai_sdk.chat import assistant, system, user


def start_interactive_session(config: ProfileConfig, api_key: str, profile: str):
    """Start an interactive session for multiple queries, using cached codebase."""
    console = Console()
    console.print("[bold green]Starting interactive session. Type 'exit' to quit.[/bold green]")
    messages: List[Union[system, user, assistant]] = []  # Maintain session messages
    cached_codebase = load_cached_codebase()  # Load cached files

    while True:
        try:
            user_input = click.prompt("Enter query (or 'exit'): ")
            if user_input.lower() == 'exit':
                console.print("[bold green]Session ended.[/bold green]")
                save_cached_codebase(cached_codebase)  # Save any updates to cache
                break

            # Build messages with session context
            full_prompt = user_input  # For simplicity; could prepend config prompt
            if not messages:
                role_from_config = config.role or "you are an expert engineer"
                messages.append(system(role_from_config))
                # Add cached codebase to initial messages if needed
                if cached_codebase:
                    files_json = json.dumps(cached_codebase, indent=2)
                    messages.append(user(f"Current codebase files:\n```json\n{files_json}\n```"))
            messages.append(user(full_prompt))

            model_used = config.model or "grok-3-mini-fast"
            temperature = config.temperature or 0

            response = call_grok(messages, model_used, api_key, temperature)
            console.print(f"[bold blue]Response:[/bold blue] {response}")

            # Update cached codebase if response is in cfold format
            try:
                response_data = json.loads(response.strip())
                if isinstance(response_data, dict) and "files" in response_data:
                    cached_codebase = apply_cfold_changes(cached_codebase, response_data["files"])
                    save_cached_codebase(cached_codebase)
                    analyze_changes({"files": cached_codebase}, response, console)
            except json.JSONDecodeError:
                console.print("[yellow]Response not in JSON format; not updating cache.[/yellow]")

            messages.append(assistant(response))  # Add response to session for context
        except Exception as e:
            console.print(f"[bold red]Error: {str(e)}[/bold red]")


def load_cached_codebase() -> List[dict]:
    """Load the cached codebase from a local file."""
    cache_file = Path(".grk_cache.json")
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text())
        except json.JSONDecodeError:
            click.echo("Warning: Cache file is corrupted. Starting with empty cache.")
    return []  # Return empty list if no cache


def save_cached_codebase(codebase: List[dict]):
    """Save the codebase to a local cache file."""
    cache_file = Path(".grk_cache.json")
    try:
        cache_file.write_text(json.dumps(codebase, indent=2))
    except Exception as e:
        click.echo(f"Warning: Failed to save cache: {str(e)}")


def apply_cfold_changes(existing: List[dict], changes: List[dict]) -> List[dict]:
    """Apply cfold changes to the existing codebase."""
    updated = existing.copy()  # Start with existing
    for change in changes:
        path = change.get("path")
        if not path or path.startswith(('/', '../')):  # Validate path
            continue  # Skip invalid paths
        for idx, item in enumerate(updated):
            if item["path"] == path:
                if change.get("delete", False):
                    updated.pop(idx)  # Delete the file
                else:
                    updated[idx] = change  # Update with new content
                break
        else:
            if not change.get("delete", False):
                updated.append(change)  # Add new file
    return updated


