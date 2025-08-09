"""Core logic for managing daemon sessions and caching."""

import json
import re
from typing import List, Union, Tuple
from pathlib import Path
import socket
import time
import click
from ..api import call_grok
from ..models import ProfileConfig
from ..config import load_brief
from ..utils import (
    get_change_summary,
    filter_protected_files,
    build_instructions_from_messages,
)
from xai_sdk.chat import assistant, system, user
import traceback


def recv_full(conn: socket.socket, size: int) -> bytes:
    """Receive exactly size bytes from the socket."""
    data = b""
    while len(data) < size:
        chunk = conn.recv(min(4096, size - len(data)))
        if not chunk:
            raise ValueError("Incomplete data received")
        data += chunk
    return data


def daemon_process(initial_file: str, config: ProfileConfig, api_key: str):
    """Run the background daemon process for session management."""
    port_file = Path(".grk_session.port")
    try:
        # Load initial codebase from file
        initial_data = json.loads(Path(initial_file).read_text())
        cached_codebase = initial_data.get("files", [])
        save_cached_codebase(cached_codebase)

        messages: List[Union[system, user, assistant]] = []
        role_from_config = config.role or "you are an expert engineer and developer"
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

        # Add initial instructions if present
        initial_instructions = initial_data.get("instructions", [])
        for instr in initial_instructions:
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

        files_json = json.dumps(cached_codebase, indent=2)
        messages.append(user(f"Current codebase files:\n```json\n{files_json}\n```"))

        model_used = config.model or "grok-4"
        temperature = config.temperature or 0

        # Set up server with dynamic port
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", 0))
        port = server.getsockname()[1]
        port_file.write_text(str(port))
        server.listen(1)

        while True:
            conn, addr = server.accept()
            try:
                # Receive length prefix (4 bytes)
                length_bytes = recv_full(conn, 4)
                length = int.from_bytes(length_bytes, "big")
                # Receive the exact data
                data_bytes = recv_full(conn, length)
                data = data_bytes.decode("utf-8")
                if not data:
                    conn.close()
                    continue
                request = json.loads(data)
                cmd = request.get("cmd")
                if cmd == "down":
                    send_response(conn, "Shutting down")
                    conn.close()
                    break
                elif cmd == "list":
                    files = [f["path"] for f in cached_codebase]
                    instructions = build_instructions_from_messages(messages)
                    response_data = {"files": files, "instructions": instructions}
                    send_response(conn, response_data)
                    conn.close()
                elif cmd == "new":
                    new_file = request["file"]
                    new_data = json.loads(Path(new_file).read_text())
                    # Reset messages
                    messages.clear()
                    messages.append(system(role_from_config))
                    # Add brief if configured
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
                        except Exception as e:
                            send_response(
                                conn, {"error": f"Failed to load brief: {str(e)}"}
                            )
                            conn.close()
                            continue
                    # Add new instructions
                    new_instructions = new_data.get("instructions", [])
                    for instr in new_instructions:
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
                    # Update cached codebase
                    cached_codebase = new_data.get("files", [])
                    save_cached_codebase(cached_codebase)
                    # Append codebase message
                    files_json = json.dumps(cached_codebase, indent=2)
                    messages.append(
                        user(f"Current codebase files:\n```json\n{files_json}\n```")
                    )
                    send_response(conn, {"message": "Instruction stack renewed."})
                    conn.close()
                elif cmd == "query":
                    prompt = request["prompt"]
                    output = request.get("output", "__temp.json")
                    input_content = request.get("input_content")
                    if input_content:
                        messages.append(
                            user(f"Additional input:\n```txt\n{input_content}\n```")
                        )
                    messages.append(user(prompt))
                    start_time = time.time()
                    response = call_grok(messages, model_used, api_key, temperature)
                    end_time = time.time()
                    thinking_time = end_time - start_time
                    messages.append(assistant(response))

                    # Postprocess response
                    cleaned_response, extracted_message = postprocess_response(response)

                    # Prepare for analysis (use cleaned_response for summary and caching)
                    input_for_analysis = {"files": [dict(**f) for f in cached_codebase]}

                    # Write output
                    try:
                        output_data = json.loads(cleaned_response)
                        if isinstance(output_data, list):
                            output_data = {"files": output_data}
                        # Filter protected files
                        brief = load_brief()
                        if brief and "files" in output_data:
                            output_data["files"] = filter_protected_files(
                                output_data["files"], {brief.file}
                            )
                        with Path(output).open("w") as f:
                            json.dump(output_data, f, indent=2)
                        # Get summary from filtered output
                        summary = get_change_summary(
                            input_for_analysis, json.dumps(output_data)
                        )
                        if "files" in output_data:
                            cached_codebase = apply_cfold_changes(
                                cached_codebase, output_data["files"]
                            )
                            save_cached_codebase(cached_codebase)
                    except json.JSONDecodeError:
                        Path(output).write_text(
                            response
                        )  # Fallback to raw if still invalid
                        summary = (
                            "No valid JSON detected; raw response saved. "
                            + get_change_summary(input_for_analysis, cleaned_response)
                        )

                    # Send summary, message, and thinking time
                    send_response(
                        conn,
                        {
                            "summary": summary,
                            "message": extracted_message,
                            "thinking_time": thinking_time,
                        },
                    )
                    conn.close()
                else:
                    send_response(conn, {"error": "Unknown command"})
                    conn.close()
            except Exception as e:
                print(f"Error handling connection: {str(e)}")
                traceback.print_exc()
                try:
                    send_response(conn, {"error": str(e)})
                except:
                    pass
                conn.close()
    except Exception as e:
        print(f"Daemon error: {str(e)}")
        traceback.print_exc()
    finally:
        server.close()
        pid_file = Path(".grk_session.pid")
        if pid_file.exists():
            pid_file.unlink()
        if port_file.exists():
            port_file.unlink()


def send_response(conn: socket.socket, resp: Union[str, dict]):
    """Send response with length prefix."""
    if isinstance(resp, str):
        resp_json = resp
    else:
        resp_json = json.dumps(resp)
    length = len(resp_json)
    length_bytes = length.to_bytes(4, "big")
    conn.send(length_bytes + resp_json.encode())


def postprocess_response(response: str) -> Tuple[str, str]:
    """Postprocess the response to extract/clean JSON and any message."""
    original_response = response.strip()
    extracted_message = ""

    # Check for markdown code block
    if original_response.startswith("```json") and original_response.endswith("```"):
        response = original_response[7:-3].strip()
    elif "```json" in original_response:
        # Extract the block if embedded
        match = re.search(r"```json\s*(.*?)\s*```", original_response, re.DOTALL)
        if match:
            extracted_message = original_response.replace(match.group(0), "").strip()
            response = match.group(1).strip()
        else:
            response = original_response
    else:
        response = original_response

    # Try to parse as JSON
    try:
        json_data = json.loads(response)
        if isinstance(json_data, list):
            return json.dumps({"files": json_data}), extracted_message
        elif isinstance(json_data, dict) and "files" in json_data:
            return json.dumps(json_data), extracted_message
        else:
            # Not a recognized format; treat as message
            return "", original_response
    except json.JSONDecodeError:
        # Fallback: find the largest valid JSON substring (e.g., embedded object)
        match = re.search(r"(\{.*\}|\[.*\])", original_response, re.DOTALL)
        if match:
            try:
                json_data = json.loads(match.group(1))
                extracted_message = original_response.replace(
                    match.group(1), ""
                ).strip()
                if isinstance(json_data, list):
                    return json.dumps({"files": json_data}), extracted_message
                elif isinstance(json_data, dict) and "files" in json_data:
                    return json.dumps(json_data), extracted_message
            except json.JSONDecodeError:
                pass
        # If no valid JSON, whole response is message
        return "", original_response


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
        if not path or path.startswith(("/", "../")):  # Validate path
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
