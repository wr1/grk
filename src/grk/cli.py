"""CLI commands for interacting with Grok LLM."""

import rich_click as click
import os
from .config import load_config, create_default_config
from .runner import run_grok
from .config_handler import list_configs
import multiprocessing
import socket
import json
from pathlib import Path
from .core.session import daemon_process
from concurrent.futures import ThreadPoolExecutor
from rich.live import Live
from rich.spinner import Spinner
from rich.console import Console
import time


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.rich_config(
    help_config=click.RichHelpConfiguration(
        # headers_style="bold cyan",
        use_markdown=True
    )
)
def main():
    """**grk**: CLI tool to interact with Grok LLM.\n\nUse single-shot commands for one-off tasks or session commands for interactive, stateful interactions."""
    pass


@main.command()
def init():
    """Initialize .grkrc with default profiles."""
    create_default_config()  # Note: This is defined in config.py


@main.command()
def list():
    """List the configurations from .grkrc with YAML syntax highlighting."""
    list_configs()


@main.command()
@click.argument("file", type=click.Path(exists=True, dir_okay=False), required=True)
@click.argument("message", required=True)
@click.option("-p", "--profile", default="default", help="The profile to use")
def run(file: str, message: str, profile: str = "default"):
    """Run the Grok LLM processing using the specified profile (single-shot mode)."""
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise click.ClickException(
            "API key is required via XAI_API_KEY environment variable."
        )
    config = load_config(profile)
    run_grok(file, message, config, api_key, profile)


@main.group(
    help="**Interactive Session Commands**\n\nManage background sessions for stateful, multi-query interactions with Grok."
)
def session():
    pass


@session.command("up")
@click.argument("file", type=click.Path(exists=True, dir_okay=False), required=True)
@click.option("-p", "--profile", default="default", help="The profile to use")
def session_up(file: str, profile: str = "default"):
    """Start a background session process with initial codebase."""
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise click.ClickException(
            "API key required via XAI_API_KEY environment variable."
        )
    config = load_config(profile)
    pid_file = Path(".grk_session.pid")
    session_file = Path(".grk_session.json")
    if pid_file.exists():
        with pid_file.open() as f:
            pid = int(f.read().strip())
        try:
            os.kill(pid, 0)
            raise click.ClickException("Session already running")
        except OSError:
            click.echo("Cleaning up stale PID file")
            pid_file.unlink()
            session_file.unlink(missing_ok=True)
    p = multiprocessing.Process(target=daemon_process, args=(file, config, api_key))
    p.start()
    pid_file.write_text(str(p.pid))
    session_file.write_text(
        json.dumps({"pid": p.pid, "profile": profile, "initial_file": file})
    )
    click.echo(f"Session started with PID {p.pid}")


@session.command("q")
@click.argument("message", required=False)
@click.option("-o", "--output", default="__temp.json", help="Output file")
@click.option(
    "-i",
    "--input",
    type=click.Path(exists=True, dir_okay=False),
    help="Additional input file",
)
@click.option(
    "-l", "--list", is_flag=True, help="List file names and prompt stack of the session"
)
def session_q(
    message: str, output: str = "__temp.json", input: str = None, list: bool = False
):
    """Send a query to the background session or list session details with -l."""
    console = Console()
    pid_file = Path(".grk_session.pid")
    session_file = Path(".grk_session.json")
    if not pid_file.exists():
        raise click.ClickException("No session running")
    if session_file.exists():
        session_data = json.loads(session_file.read_text())
        profile = session_data.get("profile", "unknown")
        initial_file = session_data.get("initial_file", "unknown")
    else:
        profile = "unknown"
        initial_file = "unknown"

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(("127.0.0.1", 61234))

        if list:
            if message:
                console.print(
                    "[yellow]Warning: Message ignored when using -l flag.[/yellow]"
                )
            request = {"cmd": "list"}
            client.send(json.dumps(request).encode())

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(client.recv, 4096)
                spinner = Spinner(
                    "dots", "[bold yellow] Fetching session details...[/bold yellow]"
                )
                if console.is_terminal:
                    with Live(
                        spinner, console=console, refresh_per_second=15, transient=True
                    ):
                        while not future.done():
                            time.sleep(0.1)
                else:
                    while not future.done():
                        time.sleep(0.1)
                response = future.result().decode()

            data = json.loads(response)
            console.print("[bold green]Session Details:[/bold green]")
            console.print(f" Profile: [cyan]{profile}[/cyan]")
            console.print(f" Initial file: [cyan]{initial_file}[/cyan]")
            console.print("[bold green]Current Files:[/bold green]")
            for f in data.get("files", []):
                console.print(f" - {f}")
            console.print("[bold green]Prompt Stack:[/bold green]")
            for i, p in enumerate(data.get("prompts", []), 1):
                truncated = p[:100] + "..." if len(p) > 100 else p
                console.print(f" {i}: {truncated}")
        else:
            if not message:
                raise click.ClickException("Message is required unless using -l flag")
            console.print(
                "[bold green]Querying grk session[/bold green] with the following settings:"
            )
            console.print(f" Profile: [cyan]{profile}[/cyan]")
            console.print(f" Initial file: [cyan]{initial_file}[/cyan]")
            console.print(f" Prompt: [cyan]{message}[/cyan]")
            console.print(f" Output: [cyan]{output}[/cyan]")
            if input:
                console.print(f" Additional input file: [cyan]{input}[/cyan]")

            input_content = Path(input).read_text() if input else None
            request = {
                "cmd": "query",
                "prompt": message,
                "output": output,
                "input_content": input_content,
            }
            client.send(json.dumps(request).encode())

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(client.recv, 4096)
                spinner = Spinner(
                    "dots", "[bold yellow] Waiting for response...[/bold yellow]"
                )
                if console.is_terminal:
                    with Live(
                        spinner, console=console, refresh_per_second=15, transient=True
                    ):
                        while not future.done():
                            time.sleep(0.1)
                else:
                    while not future.done():
                        time.sleep(0.1)
                response = future.result().decode()

            data = json.loads(response)
            console.print(f"[bold green]Summary:[/bold green] {data['summary']}")
            console.print(f"[bold green]Output written to:[/bold green] '{output}'")
    except ConnectionRefusedError:
        raise click.ClickException("Session not responding")
    finally:
        client.close()


@session.command("down")
def session_down():
    """Tear down the background session process."""
    pid_file = Path(".grk_session.pid")
    session_file = Path(".grk_session.json")
    if not pid_file.exists():
        raise click.ClickException("No session running")
    with pid_file.open() as f:
        pid = int(f.read().strip())
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(("127.0.0.1", 61234))
        client.send(json.dumps({"cmd": "down"}).encode())
        resp = client.recv(1024).decode()
        click.echo(resp)
        client.close()
    except ConnectionRefusedError:
        click.echo("Session not responding, removing PID file")
    finally:
        if pid_file.exists():
            pid_file.unlink()
        if session_file.exists():
            session_file.unlink()
        try:
            os.kill(pid, 9)
        except OSError:
            pass


if __name__ == "__main__":
    main()
