"""Session CLI commands."""

import os
import json
import time
import sys
import subprocess
import socket
from concurrent.futures import ThreadPoolExecutor
from rich.live import Live
from rich.spinner import Spinner
from rich.console import Console
from pathlib import Path
from ..config.config import load_config
from ..core.session import recv_full
from ..utils.utils import print_instruction_tree, get_synopsis, GrkException
from ..utils.logging import setup_logging
from treeparse import group, command, argument, option

logger = setup_logging()


def session_up_func(file: str, profile: str = "default"):
    """Start a background session process with initial codebase."""
    if not Path(file).exists() or Path(file).is_dir():
        raise GrkException(f"Invalid file: {file}")
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise GrkException("API key required via XAI_API_KEY environment variable.")
    config = load_config(profile)
    pid_file = Path(".grk_session.pid")
    port_file = Path(".grk_session.port")
    session_file = Path(".grk_session.json")
    log_file = Path(".grk_daemon.log")
    args_file = Path(".grk_session.args.json")
    if pid_file.exists():
        with pid_file.open() as f:
            pid = int(f.read().strip())
        try:
            os.kill(pid, 0)
            raise GrkException(
                f"Session already running (PID {pid}). Run 'grk session down' to stop it."
            )
        except OSError:
            logger.info("Cleaning up stale PID file")
            pid_file.unlink()
            port_file.unlink(missing_ok=True)
            session_file.unlink(missing_ok=True)
            log_file.unlink(missing_ok=True)

    # Serialize config and args to file
    args_dict = {
        "file": file,
        "config": config.model_dump(exclude_none=True),
        "api_key": api_key,
    }
    args_file.write_text(json.dumps(args_dict))
    # note no leading spaces
    code = """
import json
import traceback
import sys
from pathlib import Path
from grk.core.session import daemon_process
from grk.config.models import ProfileConfig
try:
    args_file = Path('.grk_session.args.json')
    args = json.loads(args_file.read_text())
    args_file.unlink()
    config = ProfileConfig(**args['config'])
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
    if os.environ.get("PYTEST_CURRENT_TEST") is not None:
        logger.info(f"Session started with PID {pid}. Logs in {log_file}")
        return
    for _ in range(10):  # Poll for up to 10 seconds
        time.sleep(1)
        if port_file.exists():
            logger.info(f"Session started with PID {pid}. Logs in {log_file}")
            return
    # If port file not found after waiting
    log_content = log_file.read_text() if log_file.exists() else "No logs available"
    raise GrkException(f"Daemon failed to start. Logs:\n{log_content}")


def session_msg_func(message: str, output: str = "__temp.json", input_file: str = None):
    """Send a message to the background session."""
    if input_file and (not Path(input_file).exists() or Path(input_file).is_dir()):
        raise GrkException(f"Invalid input file: {input_file}")
    console = Console()
    pid_file = Path(".grk_session.pid")
    port_file = Path(".grk_session.port")
    session_file = Path(".grk_session.json")
    log_file = Path(".grk_daemon.log")
    if not pid_file.exists():
        raise GrkException("No session running")
    if not port_file.exists():
        raise GrkException("Port file missing; session may have failed to start")
    port = int(port_file.read_text().strip())
    if session_file.exists():
        session_data = json.loads(session_file.read_text())
        profile = session_data.get("profile", "default")
        initial_file = session_data.get("initial_file", "unknown")
    else:
        profile = "default"
        initial_file = "unknown"
    config = load_config(profile)
    model_used = config.model or "grok-4-fast"

    # Get current instruction summary
    client_list = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_list.connect(("127.0.0.1", port))
        request_list = {"cmd": "list"}
        send_request(client_list, request_list)
        response_list = recv_response(client_list)
        data_list = json.loads(response_list)
        if "error" in data_list:
            console.print(f"[bold red]Error:[/bold red] {data_list['error']}")
            return
        instruction_list = data_list.get("instructions", [])
    except Exception as e:
        raise GrkException(f"Failed to get instruction list: {str(e)}")
    finally:
        client_list.close()

    # Prepare adding list
    adding = []
    input_content = Path(input_file).read_text() if input_file else None
    if input_content:
        input_synopsis = get_synopsis(input_content)
        adding.append(
            {
                "role": "user",
                "name": "Unnamed",
                "synopsis": f"Additional input: ```txt {input_synopsis}```",
            }
        )
    prompt_synopsis = get_synopsis(message)
    adding.append({"role": "user", "name": "Unnamed", "synopsis": prompt_synopsis})

    # Print instruction backlog and current submission separately
    print_instruction_tree(console, instruction_list, title="Instruction Backlog:")
    print_instruction_tree(console, adding, title="Current Submission:")

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(("127.0.0.1", port))

        console.print(
            "[bold green]Querying grk session[/bold green] with the following settings:"
        )
        console.print(f" Profile: [cyan]{profile}[/cyan]")
        console.print(f" Model: [yellow]{model_used}[/yellow]")
        console.print(f" Initial file: [cyan]{initial_file}[/cyan]")
        console.print(f" Prompt: [cyan]{message}[/cyan]")
        console.print(f" Output: [cyan]{output}[/cyan]")
        if input_file:
            console.print(f" Additional input file: [cyan]{input_file}[/cyan]")

        request = {
            "cmd": "query",
            "prompt": message,
            "output": output,
            "input_content": input_content,
        }
        send_request(client, request)

        response = recv_response(client, model_used=model_used)

        data = json.loads(response)
        if "error" in data:
            console.print(f"[bold red]Error:[/bold red] {data['error']}")
            return
        if data.get("message"):
            console.print(
                f"[bold green]Message from Grok:[/bold green] {data['message']}"
            )
        console.print("[bold green]Summary:[/bold green]")
        console.print(data["summary"])
        if "thinking_time" in data:
            console.print(
                f"[bold green]Thinking time:[/bold green] {data['thinking_time']:.2f} seconds"
            )
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
        raise GrkException(error_msg)
    finally:
        client.close()


def session_down_func():
    """Tear down the background session process."""
    pid_file = Path(".grk_session.pid")
    port_file = Path(".grk_session.port")
    session_file = Path(".grk_session.json")
    log_file = Path(".grk_daemon.log")
    if not pid_file.exists():
        raise GrkException("No session running")
    if not port_file.exists():
        raise GrkException("Port file missing; session may have failed to start")
    port = int(port_file.read_text().strip())
    with pid_file.open() as f:
        pid = int(f.read().strip())
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(("127.0.0.1", port))
        request = {"cmd": "down"}
        send_request(client, request)
        resp = recv_response(client)
        try:
            data = json.loads(resp)
            if "error" in data:
                logger.error(f"Error shutting down: {data['error']}")
            else:
                logger.info(resp)
        except json.JSONDecodeError:
            logger.info(resp)
        client.close()
    except ConnectionRefusedError:
        logger.info("Session not responding, removing PID file")
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


def session_list_func():
    """List file names and instruction synopses of the session."""
    console = Console()
    pid_file = Path(".grk_session.pid")
    port_file = Path(".grk_session.port")
    session_file = Path(".grk_session.json")
    log_file = Path(".grk_daemon.log")
    if not pid_file.exists():
        raise GrkException("No session running")
    if not port_file.exists():
        raise GrkException("Port file missing; session may have failed to start")
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
        request = {"cmd": "list"}
        send_request(client, request)

        response = recv_response(client)

        data = json.loads(response)
        if "error" in data:
            console.print(f"[bold red]Error from session:[/bold red] {data['error']}")
            return
        console.print("[bold green]Session Details:[/bold green]")
        console.print(f" Profile: [cyan]{profile}[/cyan]")
        console.print(f" Initial file: [cyan]{initial_file}[/cyan]")
        console.print("[bold green]Current Files:[/bold green]")
        for f in data.get("files", []):
            console.print(f" - {f}")
        instructions = data.get("instructions", [])
        print_instruction_tree(console, instructions, title="Instruction Stack:")
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
        raise GrkException(error_msg)
    finally:
        client.close()


def session_new_func(file: str):
    """Renew the instruction stack with a new file, preparing for the next message."""
    if not Path(file).exists() or Path(file).is_dir():
        raise GrkException(f"Invalid file: {file}")
    console = Console()
    pid_file = Path(".grk_session.pid")
    port_file = Path(".grk_session.port")
    session_file = Path(".grk_session.json")
    log_file = Path(".grk_daemon.log")
    if not pid_file.exists():
        raise GrkException("No session running")
    if not port_file.exists():
        raise GrkException("Port file missing; session may have failed to start")
    port = int(port_file.read_text().strip())

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(("127.0.0.1", port))
        request = {"cmd": "new", "file": file}
        send_request(client, request)

        response = recv_response(client)

        data = json.loads(response)
        if "error" in data:
            console.print(f"[bold red]Error:[/bold red] {data['error']}")
            return
        console.print(
            f"[bold green]Success:[/bold green] {data.get('message', 'Instruction stack and files renewed.')}"
        )
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
        raise GrkException(error_msg)
    finally:
        client.close()


def session_sync_func():
    """Sync internally tracked files with versions on disk."""
    console = Console()
    pid_file = Path(".grk_session.pid")
    port_file = Path(".grk_session.port")
    session_file = Path(".grk_session.json")
    log_file = Path(".grk_daemon.log")
    if not pid_file.exists():
        raise GrkException("No session running")
    if not port_file.exists():
        raise GrkException("Port file missing; session may have failed to start")
    port = int(port_file.read_text().strip())

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(("127.0.0.1", port))
        request = {"cmd": "sync"}
        send_request(client, request)

        response = recv_response(client)

        data = json.loads(response)
        if "error" in data:
            console.print(f"[bold red]Error:[/bold red] {data['error']}")
            return
        console.print(
            f"[bold green]Success:[/bold green] {data.get('message', 'Files synced.')}"
        )
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
        raise GrkException(error_msg)
    finally:
        client.close()


def session_add_func(file: str):
    """Add a file to the internal files list of the session."""
    if not Path(file).exists() or Path(file).is_dir():
        raise GrkException(f"Invalid file: {file}")
    console = Console()
    pid_file = Path(".grk_session.pid")
    port_file = Path(".grk_session.port")
    session_file = Path(".grk_session.json")
    log_file = Path(".grk_daemon.log")
    if not pid_file.exists():
        raise GrkException("No session running")
    if not port_file.exists():
        raise GrkException("Port file missing; session may have failed to start")
    port = int(port_file.read_text().strip())

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(("127.0.0.1", port))
        request = {"cmd": "add", "file": file}
        send_request(client, request)

        response = recv_response(client)

        data = json.loads(response)
        if "error" in data:
            console.print(f"[bold red]Error:[/bold red] {data['error']}")
            return
        console.print(
            f"[bold green]Success:[/bold green] {data.get('message', 'File added to session.')}"
        )
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
        raise GrkException(error_msg)
    finally:
        client.close()


def send_request(client: socket.socket, request: dict):
    """Send request with length prefix."""
    request_json = json.dumps(request)
    length = len(request_json)
    length_bytes = length.to_bytes(4, "big")
    client.send(length_bytes + request_json.encode())


def recv_response(client: socket.socket, model_used: str = None, timeout: float = 30.0) -> str:
    """Receive response with length prefix, with spinner and streaming fix.

    FIXED: Now properly handles streaming by accumulating chunks until full length received.
    Adds timeout to prevent indefinite hangs.
    """
    import select
    console = Console()
    wait_text = (
        f"[bold yellow] Waiting for {model_used} response...[/bold yellow]"
        if model_used
        else "[bold yellow] Waiting for response...[/bold yellow]"
    )
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=1) as executor:
        # First, receive length prefix (4 bytes)
        future_length = executor.submit(recv_full, client, 4)
        spinner = Spinner("dots", wait_text)
        if console.is_terminal:
            with Live(spinner, console=console, refresh_per_second=15, transient=True):
                while not future_length.done() and (time.time() - start_time) < timeout:
                    time.sleep(0.1)
        else:
            while not future_length.done() and (time.time() - start_time) < timeout:
                time.sleep(0.1)
        
        if (time.time() - start_time) >= timeout:
            raise GrkException(f"Response timeout after {timeout}s")
        
        length_bytes = future_length.result()
        length = int.from_bytes(length_bytes, "big")

        # FIXED: Accumulate data in chunks until we have exactly 'length' bytes
        data_bytes = b""
        while len(data_bytes) < length:
            remaining = length - len(data_bytes)
            chunk_size = min(4096, remaining)
            
            # Use select to check if data available (non-blocking)
            ready, _, _ = select.select([client], [], [], 1.0)
            if not ready:
                if (time.time() - start_time) >= timeout:
                    raise GrkException(f"Response timeout after {timeout}s")
                continue
            
            chunk = client.recv(chunk_size)
            if not chunk:
                raise GrkException("Daemon closed connection prematurely")
            data_bytes += chunk
            
            # Update spinner for terminal
            if console.is_terminal:
                with Live(spinner, console=console, refresh_per_second=15, transient=True):
                    pass

        return data_bytes.decode("utf-8")


session_grp = group(
    name="session",
    help="Interactive Session Mode, manage background sessions for stateful, multi-query interactions with Grok.",
)

up_cmd = command(
    name="up",
    help="Start a background session process with initial codebase.",
    callback=session_up_func,
    sort_key=-10,
    arguments=[
        argument(name="file", arg_type=str, sort_key=0),
    ],
    options=[
        option(
            flags=["--profile", "-p"],
            help="The profile to use",
            arg_type=str,
            default="default",
            sort_key=0,
        ),
    ],
)
session_grp.commands.append(up_cmd)

msg_cmd = command(
    name="msg",
    help="Send a message to the background session.",
    callback=session_msg_func,
    sort_key=-5,
    arguments=[
        argument(name="message", arg_type=str, sort_key=0),
    ],
    options=[
        option(
            flags=["--output", "-o"],
            help="Output file",
            arg_type=str,
            default="__temp.json",
            sort_key=0,
        ),
        option(
            flags=["--input_file", "-i"],
            help="Additional input file",
            arg_type=str,
            default=None,
            sort_key=1,
        ),
    ],
)
session_grp.commands.append(msg_cmd)

down_cmd = command(
    name="down",
    help="Tear down the background session process.",
    callback=session_down_func,
)
session_grp.commands.append(down_cmd)

list_session_cmd = command(
    name="list",
    help="List file names and instruction synopses of the session.",
    callback=session_list_func,
)
session_grp.commands.append(list_session_cmd)

new_cmd = command(
    name="new",
    help="Renew the instruction stack with a new cfold file, preparing for the next message.",
    callback=session_new_func,
    arguments=[
        argument(name="file", arg_type=str, sort_key=0),
    ],
)
session_grp.commands.append(new_cmd)

sync_cmd = command(
    name="sync",
    help="Sync internally tracked files with versions on disk.",
    callback=session_sync_func,
)
session_grp.commands.append(sync_cmd)

add_cmd = command(
    name="add",
    help="Add a file to the internal files list of the session.",
    callback=session_add_func,
    arguments=[
        argument(name="file", arg_type=str, sort_key=0),
    ],
)
session_grp.commands.append(add_cmd)
