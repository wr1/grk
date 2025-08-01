"""Core logic for running Grok LLM interactions."""

import json
from typing import List, Union
from xai_sdk.chat import assistant, system, user
from pathlib import Path
from .api import call_grok
import time
from rich.console import Console
from concurrent.futures import ThreadPoolExecutor
from rich.live import Live
from rich.spinner import Spinner
import click
from .config import ProfileConfig
from .utils import analyze_changes


def run_grok(file: str, message: str, config: ProfileConfig, api_key: str):
    """Execute the Grok LLM run logic with given inputs and config."""
    model_used = config.model or "grok-3-mini-fast"
    role_from_config = (
        config.role or "you are an expert python programmer, writing clean code"
    )
    output_file = config.output or "output.json"
    json_out_file = config.json_out or "meta_output.json"
    prompt_prepend = config.prompt_prepend or ""
    temperature = config.temperature or 0

    try:
        file_content = Path(file).read_text()
    except Exception as e:
        raise click.ClickException(f"Failed to read file: {str(e)}")

    messages: List[Union[system, user, assistant]] = []
    full_prompt = prompt_prepend + message
    if role_from_config:
        messages.append(system(role_from_config))

    try:
        input_data = json.loads(file_content)
        is_cfold = (
            isinstance(input_data, dict)
            and "instructions" in input_data
            and "files" in input_data
        )
        if is_cfold:
            for instr in input_data["instructions"]:
                role = instr["type"]
                if role == "system":
                    msg = system(instr["content"])
                elif role == "user":
                    msg = user(instr["content"])
                elif role == "assistant":
                    msg = assistant(instr["content"])
                else:
                    raise ValueError(f"Unknown message type: {role}")
                if role == "user" and instr.get("name"):
                    msg.name = instr["name"]
                messages.append(msg)
            files_json = json.dumps(input_data["files"], indent=2)
            messages.append(
                user(f"Current codebase files:\n```json\n{files_json}\n```")
            )
            messages.append(user(full_prompt))
        else:
            messages.append(user(file_content))
            messages.append(user(full_prompt))
    except json.JSONDecodeError:
        messages.append(user(file_content))
        messages.append(user(full_prompt))
        is_cfold = False
        input_data = None

    console = Console()
    console.print("[bold green]Running grk[/bold green] with the following settings:")
    console.print(f" Profile: [cyan]{config.profile}[/cyan]")
    console.print(f" Model: [yellow]{model_used}[/yellow]")
    console.print(f" Role: [cyan]{role_from_config}[/cyan]")
    console.print(f" File: [cyan]{file}[/cyan]")
    console.print(f" Temperature: [red]{temperature}[/red]")

    console.print("[bold green]Message stack:[/bold green]")
    for i, msg in enumerate(messages):
        role = msg.role
        content = msg.content
        truncated = content[:200] + "..." if len(content) > 200 else content
        if i == len(messages) - 1 and role == "user":
            console.print(f"[{role.upper()}]: {content}")
        else:
            console.print(f"[{role.upper()}]: {truncated}")
        if hasattr(msg, "name") and msg.name:
            console.print(f"  Name: {msg.name}")

    console.print("[bold green]Calling Grok API...[/bold green]")
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(
            call_grok,
            messages,
            model_used,
            api_key,
            temperature,
        )
        if console.is_terminal:
            spinner = Spinner(
                "dots", "[bold yellow] Waiting for API response...[/bold yellow]"
            )
            with Live(spinner, console=console, refresh_per_second=15, transient=True):
                while not future.done():
                    time.sleep(0.1)
        else:
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
                    "used_profile": config.profile,
                },
                f,
                indent=2,
            )
        click.echo(f"Response saved to {output_file} and {json_out_file}")

        if is_cfold:
            analyze_changes(input_data, response, console)
    except Exception as e:
        raise click.ClickException(f"Failed to write output: {str(e)}")

