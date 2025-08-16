"""Core logic for running Grok LLM interactions."""

import json
from typing import List, Union
from pathlib import Path
from .api import call_grok
import time
from rich.console import Console
from concurrent.futures import ThreadPoolExecutor
from rich.live import Live
from rich.spinner import Spinner
import click
from .config import ProfileConfig, load_brief
from .utils import (
    analyze_changes,
    filter_protected_files,
    build_instructions_from_messages,
    print_instruction_tree,
)
from xai_sdk.chat import assistant, system, user


def run_grok(
    file: str,
    message: str,
    config: ProfileConfig,
    api_key: str,
    profile: str = "default",
):
    """Execute the Grok LLM run logic with given inputs and config."""
    model_used = config.model or "grok-4"
    role_from_config = config.role or "you are an expert engineer and developer"
    output_file = config.output or "output.json"
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

    # Add brief if configured
    brief = load_brief()
    if brief:
        try:
            brief_content = Path(brief.file).read_text()
            brief_role = brief.role.lower()
            if brief_role == "system":
                messages.append(system(brief_content))
            elif brief_role == "user":
                messages.append(user(brief_content))
            elif brief_role == "assistant":
                messages.append(assistant(brief_content))
            else:
                raise ValueError(f"Invalid role for brief: {brief_role}")
        except FileNotFoundError:
            click.echo(f"Warning: Brief file '{brief.file}' not found, skipping.")
        except Exception as e:
            raise click.ClickException(f"Failed to load brief: {str(e)}")

    try:
        input_data = json.loads(file_content)
        if isinstance(input_data, list):
            input_data = {"instructions": [], "files": input_data}
        elif isinstance(input_data, dict):
            if "files" in input_data:
                input_data["instructions"] = input_data.get("instructions", [])

        is_cfold = (
            isinstance(input_data, dict)
            and "instructions" in input_data
            and "files" in input_data
        )

        if is_cfold:
            for instr in input_data["instructions"]:
                role = instr["type"]
                content = instr["content"]
                if role == "system":
                    msg = system(content)
                elif role == "user":
                    msg = user(content)
                elif role == "assistant":
                    msg = assistant(content)
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
    console.print(f" Profile: [cyan]{profile}[/cyan]")
    console.print(f" Model: [yellow]{model_used}[/yellow]")
    console.print(f" Role: [cyan]{role_from_config}[/cyan]")
    console.print(f" File: [cyan]{file}[/cyan]")
    console.print(f" Temperature: [red]{temperature}[/red]")
    console.print(f" Prompt: [cyan]{message}[/cyan]")

    # Print instruction summary
    instruction_list = build_instructions_from_messages(messages)
    print_instruction_tree(console, instruction_list)

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
                "dots",
                f"[bold yellow] Waiting for {model_used} response...[/bold yellow]",
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
        # Always write the response, format if valid JSON for cfold
        if is_cfold:
            response_to_parse = response.strip()
            if response_to_parse.startswith("```json") and response_to_parse.endswith(
                "```"
            ):
                inner = response_to_parse[7:-3].strip()
                response_to_parse = inner
            try:
                output_data = json.loads(response_to_parse)
                if isinstance(output_data, list):
                    output_data = {"files": output_data}
                # Filter protected files
                brief = load_brief()
                if brief and "files" in output_data:
                    output_data["files"] = filter_protected_files(
                        output_data["files"], {brief.file}
                    )
                with Path(output_file).open("w") as f:
                    json.dump(output_data, f, indent=2)
                # Analyze filtered output
                analyze_changes(input_data, json.dumps(output_data), console)
            except json.JSONDecodeError:
                console.print(
                    "[yellow]Warning: Response is not valid JSON, writing as text.[/yellow]"
                )
                Path(output_file).write_text(response)
                if input_data:
                    analyze_changes(input_data, response, console)
        else:
            Path(output_file).write_text(response)
        console.print(f"[bold green]Output written to:[/bold green] '{output_file}'")
    except Exception as e:
        raise click.ClickException(f"Failed to write output: {str(e)}")
