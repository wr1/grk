"""Utility functions for Grok CLI, including caching helpers."""

import json
import difflib
from collections import defaultdict
from rich.console import Console
from pathlib import Path
from typing import List, Set, Dict, Any

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
    """Get a detailed string summary of changes from response in cfold format, including file tree and diffs."""
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
        all_affected = changed_files + new_files + deleted_files
        if not all_affected:
            return "= No changes detected."

        # Build file tree
        tree = defaultdict(list)
        for path in all_affected:
            parts = path.split('/')
            current = tree
            for part in parts[:-1]:
                if part not in current:
                    current[part] = defaultdict(list)
                current = current[part]
            current[parts[-1]] = path  # Leaf is the full path

        def build_tree_str(node, prefix=""):
            lines = []
            items = sorted(node.items())
            for i, (key, value) in enumerate(items):
                is_last = i == len(items) - 1
                if isinstance(value, defaultdict):
                    lines.append(f"{prefix}{'└── ' if is_last else '├── '}{key}/")
                    lines.extend(build_tree_str(value, prefix + ('    ' if is_last else '│   ')))
                else:
                    status = " (modified)" if value in changed_files else " (new)" if value in new_files else " (deleted)"
                    lines.append(f"{prefix}{'└── ' if is_last else '├── '}{key}{status}")
            return lines

        tree_str = "\n".join(build_tree_str(tree))

        # Build diffs for changed files
        diff_strs = []
        for path in changed_files:
            old_lines = input_files[path].splitlines()
            new_lines = output_files[path].splitlines()
            diff = difflib.unified_diff(old_lines, new_lines, fromfile=path + " (old)", tofile=path + " (new)")
            diff_str = "\n".join(diff)
            diff_strs.append(f"Diff for {path}:\n{diff_str}\n")

        summary_lines = [tree_str]
        if diff_strs:
            summary_lines.append("\nDetailed diffs:")
            summary_lines.extend(diff_strs)

        if new_files:
            summary_lines.append(f"New files: {', '.join(new_files)}")
        if deleted_files:
            summary_lines.append(f"Deleted files: {', '.join(deleted_files)}")

        return "\n".join(summary_lines)
    except json.JSONDecodeError:
        return "Response not in JSON format; no changes applied."

def filter_protected_files(files_list: List[dict], protected_paths: Set[str]) -> List[dict]:
    """Filter out changes to protected files from the list."""
    filtered = []
    for f in files_list:
        if f["path"] in protected_paths:
            continue
        filtered.append(f)
    return filtered

def build_instructions_from_messages(messages: List) -> List[Dict[str, Any]]:
    """Build list of instruction dicts from messages for summary, skipping empty content."""
    instructions = []
    for msg in messages:
        role = msg.role
        name = getattr(msg, 'name', "Unnamed")
        content = msg.content
        content_str = content if isinstance(content, str) else ' '.join(content) if isinstance(content, (list, tuple)) else str(content)
        if not content_str.strip():
            continue  # Skip empty instructions
        synopsis = content_str[:100].strip() + ("..." if len(content_str) > 100 else "")
        synopsis = synopsis.replace("\n", " ")
        instructions.append({"role": role, "name": name, "synopsis": synopsis})
    return instructions

def print_instruction_tree(console: Console, instructions: List[Dict[str, Any]], adding: List[Dict[str, Any]] = None, title: str = "Instruction Summary:"):
    """Print instruction summary in a tree-like format."""
    if adding is None:
        adding = []
    all_instr = instructions + adding
    if not all_instr:
        console.print("[yellow]No instructions.[/yellow]")
        return
    console.print(f"[bold green]{title}[/bold green]")
    lines = []
    for idx, instr in enumerate(all_instr):
        is_last = idx == len(all_instr) - 1
        prefix = "└── " if is_last else "├── "
        role = instr.get('role', 'unknown')
        # Map integer-like roles to spelled-out versions
        role_map = {
            '1': 'system',
            '2': 'user',
            '3': 'assistant'
        }
        role_str = str(role)
        role = role_map.get(role_str, role)
        name = instr.get('name', 'Unnamed')
        synopsis = instr.get('synopsis', '')
        name_str = f" ({name})" if name != "Unnamed" else ""
        lines.append(f"{prefix}{role}{name_str}: {synopsis}")
    console.print("\n".join(lines))









