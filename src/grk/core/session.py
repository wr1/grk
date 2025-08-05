"""Core logic for managing daemon sessions and caching."""

import json
import re
from typing import List, Union, Tuple
from pathlib import Path
import socket
import os
import click
from rich.console import Console
from ..api import call_grok
from ..models import ProfileConfig
from ..utils import get_change_summary
from xai_sdk.chat import assistant, system, user

def daemon_process(initial_file: str, config: ProfileConfig, api_key: str):
    """Run the background daemon process for session management."""
    try:
        # Load initial codebase from file
        initial_data = json.loads(Path(initial_file).read_text())
        cached_codebase = initial_data.get("files", [])
        save_cached_codebase(cached_codebase)

        messages: List[Union[system, user, assistant]] = []
        role_from_config = config.role or "you are an expert engineer and developer"
        messages.append(system(role_from_config))
        files_json = json.dumps(cached_codebase, indent=2)
        messages.append(user(f"Current codebase files:\n```json\n{files_json}\n```"))

        model_used = config.model or "grok-3-mini-fast"
        temperature = config.temperature or 0

        # Set up server
        PORT = 61234
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("127.0.0.1", PORT))
        server.listen(1)

        while True:
            conn, addr = server.accept()
            data = conn.recv(4096).decode('utf-8')
            if not data:
                conn.close()
                continue
            request = json.loads(data)
            cmd = request.get("cmd")
            if cmd == "down":
                conn.send("Shutting down".encode())
                conn.close()
                break
            elif cmd == "list":
                files = [f["path"] for f in cached_codebase]
                prompts = []
                for msg in messages[2:]:  # Skip initial system and files message
                    if isinstance(msg, user):
                        prompts.append(msg.content)
                response_data = {"files": files, "prompts": prompts}
                conn.send(json.dumps(response_data).encode())
                conn.close()
            elif cmd == "query":
                prompt = request["prompt"]
                output = request.get("output", "__temp.json")
                input_content = request.get("input_content")
                if input_content:
                    messages.append(user(f"Additional input:\n```txt\n{input_content}\n```"))
                messages.append(user(prompt))
                response = call_grok(messages, model_used, api_key, temperature)
                messages.append(assistant(response))

                # Postprocess response
                cleaned_response, extracted_message = postprocess_response(response)

                # Prepare for analysis (use cleaned_response for summary and caching)
                input_for_analysis = {"files": [dict(**f) for f in cached_codebase]}
                summary = get_change_summary(input_for_analysis, cleaned_response)

                # Write output
                try:
                    output_data = json.loads(cleaned_response)
                    if isinstance(output_data, list):
                        output_data = {"files": output_data}
                    with Path(output).open("w") as f:
                        json.dump(output_data, f, indent=2)
                    if "files" in output_data:
                        cached_codebase = apply_cfold_changes(cached_codebase, output_data["files"])
                        save_cached_codebase(cached_codebase)
                except json.JSONDecodeError:
                    Path(output).write_text(response)  # Fallback to raw if still invalid
                    summary = "No valid JSON detected; raw response saved. " + summary

                # Send summary and message
                conn.send(json.dumps({"summary": summary, "message": extracted_message}).encode())
                conn.close()
            else:
                conn.close()
    except Exception as e:
        print(f"Daemon error: {str(e)}")
    finally:
        server.close()
        pid_file = Path(".grk_session.pid")
        if pid_file.exists():
            pid_file.unlink()

def postprocess_response(response: str) -> Tuple[str, str]:
    """Postprocess the response to extract/clean JSON and any message."""
    response = response.strip()
    extracted_message = ""

    # Check for markdown code block
    if response.startswith("```json") and response.endswith("```"):
        response = response[7:-3].strip()
    elif "```json" in response:
        # Extract the block if embedded
        match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
        if match:
            response = match.group(1).strip()
            extracted_message = response.replace(match.group(0), "").strip()

    # Try to parse as JSON
    try:
        json_data = json.loads(response)
        if isinstance(json_data, list):
            return json.dumps({"files": json_data}, indent=2), extracted_message
        elif isinstance(json_data, dict) and "files" in json_data:
            return json.dumps(json_data, indent=2), extracted_message
        else:
            # Not a recognized format; treat as message
            return "", response
    except json.JSONDecodeError:
        # Fallback: find the largest valid JSON substring (e.g., embedded object)
        match = re.search(r"(\{.*?\}|\[.*?\])", response, re.DOTALL)
        if match:
            try:
                json_data = json.loads(match.group(1))
                extracted_message = response.replace(match.group(1), "").strip()
                if isinstance(json_data, list):
                    return json.dumps({"files": json_data}, indent=2), extracted_message
                elif isinstance(json_data, dict) and "files" in json_data:
                    return json.dumps(json_data, indent=2), extracted_message
            except json.JSONDecodeError:
                pass
        # If no valid JSON, whole response is message
        return "", response

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



