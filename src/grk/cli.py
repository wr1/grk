"""CLI commands for interacting with Grok LLM."""

import rich_click as click
import os
from .config import load_config, create_default_config
from .runner import run_grok
from .config_handler import list_configs
import socket
import json
from pathlib import Path
from .core.session import recv_full, daemon_process
import time
from concurrent.futures import ThreadPoolExecutor
from rich.live import Live
from rich.spinner import Spinner
from rich.console import Console
import sys
import subprocess
import traceback


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.rich_config(help_config=click.RichHelpConfiguration(use_markdown=True))
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


@main.command("up")
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
    port_file = Path(".grk_session.port")
    session_file = Path(".grk_session.json")
    log_file = Path(".grk_daemon.log")
    if pid_file.exists():
        with pid_file.open() as f:
            pid = int(f.read().strip())
        try:
            os.kill(pid, 0)
            raise click.ClickException("Session already running")
        except OSError:
            click.echo("Cleaning up stale PID file")
            pid_file.unlink()
            port_file.unlink(missing_ok=True)
            session_file.unlink(missing_ok=True)
            log_file.unlink(missing_ok=True)

    # Serialize config and args for subprocess
    config_dict = config.model_dump(exclude_none=True)
    config_json = json.dumps(config_dict)
    args = json.dumps({"file": file, "config_json": config_json, "api_key": api_key})
    # note no leading spaces
    code = f"""
import json
import traceback
import sys
from grk.core.session import daemon_process
from grk.models import ProfileConfig
try:
    args = json.loads({json.dumps(args)})
    config = ProfileConfig(**json.loads(args['config_json']))
    daemon_process(args['file'], config, args['api_key'])
except Exception as e:
    print("Daemon error:", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
    """

    creation_flags = 0
    if sys.platform.startswith("win"):
        creation_flags = (
            subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        )
    with open(log_file, "w") as log:
        p = subprocess.Popen(
            [sys.executable, "-c", code],
            stdout=log,
            stderr=log,
            creationflags=creation_flags,
            start_new_session=not sys.platform.startswith("win"),
        )
    pid = p.pid
    pid_file.write_text(str(pid))
    session_file.write_text(
        json.dumps({"pid": pid, "profile": profile, "initial_file": file})
    )
    # Wait for daemon to start and write port file
    for _ in range(10):  # Poll for up to 10 seconds
        time.sleep(1)
        if port_file.exists():
            click.echo(f"Session started with PID {pid}. Logs in {log_file}")
            return
    # If port file not found after waiting
    log_content = log_file.read_text() if log_file.exists() else "No logs available"
    raise click.ClickException(f"Daemon failed to start. Logs:\n{log_content}")


@main.command("q")
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
    """Send a message to the background session or list session details with -l."""
    console = Console()
    pid_file = Path(".grk_session.pid")
    port_file = Path(".grk_session.port")
    session_file = Path(".grk_session.json")
    log_file = Path(".grk_daemon.log")
    if not pid_file.exists():
        raise click.ClickException("No session running")
    if not port_file.exists():
        raise click.ClickException("Port file missing; session may have failed to start")
    port = int(port_file.read_text().strip())
    if session_file.exists():
        session_data = json.loads(session_file.read_text())
        profile = session_data.get("profile", "unknown")
        initial_file = session_data.get("initial_file", "unknown")
    else:
        profile = "unknown"
        initial_file = "unknown"

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(("127.0.0.1", port))

        if list:
            if message:
                console.print(
                    "[yellow]Warning: Message ignored when using -l flag.[/yellow]"
                )
            request = {"cmd": "list"}
            send_request(client, request)

            response = recv_response(client)

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
            send_request(client, request)

            response = recv_response(client)

            data = json.loads(response)
            if data.get("message"):
                console.print(
                    f"[bold green]Message from Grok:[/bold green] {data['message']}"
                )
            console.print(f"[bold green]Summary:[/bold green] {data['summary']}")
            console.print(f"[bold green]Output written to:[/bold green] '{output}'")
    except ConnectionRefusedError:
        error_msg = "Session not responding."
        if pid_file.exists():
            with pid_file.open() as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, 0)
                error_msg += " Process is running but not listening."
            except OSError:
                error_msg += " Process is not running. Cleaning up."
                pid_file.unlink()
                port_file.unlink(missing_ok=True)
                session_file.unlink(missing_ok=True)
        if log_file.exists():
            log_content = log_file.read_text()
            error_msg += f"\nDaemon log:\n{log_content}"
        else:
            error_msg += " No daemon log found."
        raise click.ClickException(error_msg)
    finally:
        client.close()


def send_request(client: socket.socket, request: dict):
    """Send request with length prefix."""
    request_json = json.dumps(request)
    length = len(request_json)
    length_bytes = length.to_bytes(4, "big")
    client.send(length_bytes + request_json.encode())


def recv_response(client: socket.socket) -> str:
    """Receive response with length prefix, with spinner."""
    console = Console()
    with ThreadPoolExecutor(max_workers=1) as executor:
        # First, receive length
        future_length = executor.submit(recv_full, client, 4)
        spinner = Spinner("dots", "[bold yellow] Waiting for response...[/bold yellow]")
        if console.is_terminal:
            with Live(spinner, console=console, refresh_per_second=15, transient=True):
                while not future_length.done():
                    time.sleep(0.1)
        else:
            while not future_length.done():
                time.sleep(0.1)
        length_bytes = future_length.result()
        length = int.from_bytes(length_bytes, "big")

        # Then, receive data
        future_data = executor.submit(recv_full, client, length)
        if console.is_terminal:
            with Live(spinner, console=console, refresh_per_second=15, transient=True):
                while not future_data.done():
                    time.sleep(0.1)
        else:
            while not future_data.done():
                time.sleep(0.1)
        data_bytes = future_data.result()
        return data_bytes.decode("utf-8")


@main.command("down")
def session_down():
    """Tear down the background session process."""
    pid_file = Path(".grk_session.pid")
    port_file = Path(".grk_session.port")
    session_file = Path(".grk_session.json")
    log_file = Path(".grk_daemon.log")
    if not pid_file.exists():
        raise click.ClickException("No session running")
    if not port_file.exists():
        raise click.ClickException("Port file missing; session may have failed to start")
    port = int(port_file.read_text().strip())
    with pid_file.open() as f:
        pid = int(f.read().strip())
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(("127.0.0.1", port))
        request = {"cmd": "down"}
        send_request(client, request)
        resp = recv_response(client)
        click.echo(resp)
        client.close()
    except ConnectionRefusedError:
        click.echo("Session not responding, removing PID file")
    finally:
        if pid_file.exists():
            pid_file.unlink()
        if port_file.exists():
            port_file.unlink()
        if session_file.exists():
            session_file.unlink()
        if log_file.exists():
            log_file.unlink()
        try:
            os.kill(pid, 9)
        except OSError:
            pass


if __name__ == "__main__":
    main()


