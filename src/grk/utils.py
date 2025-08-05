"""Utility functions for Grok CLI, including caching helpers."""

import json
from rich.console import Console
from pathlib import Path

def analyze_changes(input_data: dict, response: str, console: Console):
    """Analyze and print changes if response is cfold format."""
    try:
        response_to_parse = response.strip()
        if response_to_parse.startswith("```json") and response_to_parse.endswith("```"):
            response_to_parse = response_to_parse[7:-3].strip()
        output_data = json.loads(response_to_parse)

        if isinstance(output_data, list):
            output_files_list = output_data
        elif isinstance(output_data, dict) and "files" in output_data:
            output_files_list = output_data["files"]
        else:
            console.print("[yellow]Response is not a recognized cfold format, skipping change analysis.[/yellow]")
            return

        output_files = {}
        deleted_files = []
        for f in output_files_list:
            path = f["path"]
            if f.get("delete", False):
                deleted_files.append(path)
            elif "content" in f:
                output_files[path] = f["content"]

        input_files = {}
        for f in input_data.get("files", []):
            if not f.get("delete", False) and "content" in f:
                input_files[f["path"]] = f["content"]

        changed_files = [path for path in output_files if path in input_files and output_files[path] != input_files[path]]
        new_files = [path for path in output_files if path not in input_files]

        console.print("[bold green]Suggested changes:[/bold green]")
        if changed_files:
            console.print("Changed files:")
            for path in changed_files:
                console.print(f" - {path}")
        else:
            console.print("No changed files.")

        if new_files:
            console.print("New files:")
            for path in new_files:
                console.print(f" - {path}")
        else:
            console.print("No new files.")

        if deleted_files:
            console.print("Deleted files:")
            for path in deleted_files:
                console.print(f" - {path}")
        else:
            console.print("No deleted files.")
    except json.JSONDecodeError:
        console.print("[yellow]Response is not valid JSON, skipping change analysis.[/yellow]")

def get_change_summary(input_data: dict, response: str) -> str:
    """Get a string summary of changes from response in cfold format."""
    try:
        response_to_parse = response.strip()
        if response_to_parse.startswith("```json") and response_to_parse.endswith("```"):
            response_to_parse = response_to_parse[7:-3].strip()
        output_data = json.loads(response_to_parse)
        if isinstance(output_data, list):
            output_files_list = output_data
        elif isinstance(output_data, dict) and "files" in output_data:
            output_files_list = output_data["files"]
        else:
            return "= No file changes detected."
        output_files = {f["path"]: f["content"] for f in output_files_list if not f.get("delete", False) and "content" in f}
        deleted_files = [f["path"] for f in output_files_list if f.get("delete", False)]
        input_files = {f["path"]: f["content"] for f in input_data.get("files", []) if not f.get("delete", False) and "content" in f}
        changed_files = [path for path in output_files if path in input_files and output_files[path] != input_files[path]]
        new_files = [path for path in output_files if path not in input_files]
        summary_lines = []
        if changed_files:
            summary_lines.append(f"modified files {', '.join(changed_files)}")
        if new_files:
            summary_lines.append(f"new files {', '.join(new_files)}")
        if deleted_files:
            summary_lines.append(f"deleted files {', '.join(deleted_files)}")
        if not summary_lines:
            return "= No changes detected."
        return "= " + ", ".join(summary_lines)
    except json.JSONDecodeError:
        return "Response not in JSON format; no changes applied."



