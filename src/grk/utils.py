"""Utility functions for Grok CLI."""

import json
from rich.console import Console


def analyze_changes(input_data: dict, response: str, console: Console):
    """Analyze and print changes if response is cfold format."""
    try:
        output_data = json.loads(response)
        if "files" in output_data:
            input_files = {f["path"]: f["content"] for f in input_data["files"]}
            output_files = {
                f["path"]: f["content"] for f in output_data["files"]
            }

            changed_files = [
                path
                for path in output_files
                if path in input_files
                and output_files[path] != input_files[path]
                and output_files[path] != "# DELETE"
            ]
            new_files = [
                path
                for path in output_files
                if path not in input_files and output_files[path] != "# DELETE"
            ]
            deleted_files = [
                path
                for path in output_files
                if output_files[path] == "# DELETE"
            ]

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
        console.print(
            "[yellow]Response is not valid JSON, skipping change analysis.[/yellow]"
        )

