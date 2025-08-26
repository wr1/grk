"""Tests for utility functions in grk.utils."""

from rich.console import Console
from grk.utils import (
    get_synopsis,
    analyze_changes,
    get_change_summary,
    filter_protected_files,
    build_instructions_from_messages,
    print_instruction_tree,
)
import re


class MockMessage:
    def __init__(self, role, content, name=None):
        self.role = role
        self.content = content
        if name:
            self.name = name


def strip_ansi(text: str) -> str:
    """Strip ANSI escape codes from text."""
    ansi_escape = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def test_get_synopsis():
    """Test get_synopsis extraction."""
    assert get_synopsis("Line1\n\nLine2") == "Line1"
    assert get_synopsis("") == ""
    long_line = "a" * 150
    assert get_synopsis(long_line) == "a" * 100 + "..."


def test_analyze_changes_valid_json(capsys):
    """Test analyze_changes with valid JSON."""
    input_data = {"files": [{"path": "file1.txt", "content": "old"}]}
    response = '{"files": [{"path": "file1.txt", "content": "new"}, {"path": "file2.txt", "content": "added"}, {"path": "file3.txt", "delete": true}]}'
    console = Console()
    analyze_changes(input_data, response, console)
    captured = capsys.readouterr()
    assert "Changed files:" in captured.out
    assert "New files:" in captured.out
    assert "Deleted files:" in captured.out


def test_analyze_changes_invalid_json(capsys):
    """Test analyze_changes with invalid JSON."""
    input_data = {}
    response = "invalid"
    console = Console()
    analyze_changes(input_data, response, console)
    captured = capsys.readouterr()
    assert "Response is not valid JSON" in captured.out


def test_get_change_summary_no_changes():
    """Test get_change_summary with no changes."""
    input_data = {}
    response = '{"files": []}'
    assert "No changes detected." in get_change_summary(input_data, response)


def test_get_change_summary_with_diffs():
    """Test get_change_summary including diffs."""
    input_data = {"files": [{"path": "file.txt", "content": "old"}]}
    response = '{"files": [{"path": "file.txt", "content": "new"}]}'
    summary = get_change_summary(input_data, response)
    assert "Diff for file.txt:" in summary
    assert "-old" in summary
    assert "+new" in summary


def test_filter_protected_files():
    """Test filter_protected_files removes protected paths."""
    files_list = [{"path": "protected.txt"}, {"path": "normal.txt"}]
    protected = {"protected.txt"}
    filtered = filter_protected_files(files_list, protected)
    assert len(filtered) == 1
    assert filtered[0]["path"] == "normal.txt"


def test_build_instructions_from_messages():
    """Test building instructions from messages, skipping empty."""
    messages = [
        MockMessage(3, "System message"),
        MockMessage(1, "User message", name="User1"),
        MockMessage(2, "Assistant message"),
        MockMessage(1, ""),  # Empty, should be skipped
    ]
    instructions = build_instructions_from_messages(messages)
    assert len(instructions) == 3
    assert instructions[0]["synopsis"] == "System message"
    assert instructions[1]["name"] == "User1"
    assert instructions[1]["synopsis"] == "User message"
    assert instructions[2]["synopsis"] == "Assistant message"


def test_print_instruction_tree(capsys):
    """Test printing instruction tree with colors and filtering."""
    console = Console(force_terminal=True)
    instructions = [
        {"role": "system", "name": "Sys1", "synopsis": "System msg"},
        {"role": "user", "name": "User1", "synopsis": "User msg"},
        {"role": "assistant", "synopsis": ""},  # Empty, skipped
        {"role": "assistant", "synopsis": "Assistant msg"},
    ]
    print_instruction_tree(console, instructions)
    captured = capsys.readouterr()
    stripped = strip_ansi(captured.out)
    assert "Instruction Summary:" in stripped
    assert "system (Sys1): System msg" in stripped
    assert "user (User1): User msg" in stripped
    assert "assistant: Assistant msg" in stripped
    assert stripped.count("\n") == 4  # Title + 3 lines + final newline


def test_print_instruction_tree_no_instructions(capsys):
    """Test printing when no instructions after filtering."""
    console = Console(force_terminal=True)
    print_instruction_tree(console, [])
    captured = capsys.readouterr()
    stripped = strip_ansi(captured.out)
    assert "No instructions." in stripped


def test_get_change_summary_invalid_json():
    """Test get_change_summary with invalid JSON."""
    input_data = {}
    response = "invalid"
    assert "Response not in JSON format" in get_change_summary(input_data, response)


def test_analyze_changes_not_recognized(capsys):
    """Test analyze_changes with unrecognized format."""
    input_data = {}
    response = '{"other": []}'
    console = Console()
    analyze_changes(input_data, response, console)
    captured = capsys.readouterr()
    assert "not a recognized cfold format" in captured.out


def test_build_instructions_complex_content():
    """Test building instructions with complex content."""
    messages = [MockMessage(1, [{"text": "Part1"}, {"content": "Part2"}])]
    instructions = build_instructions_from_messages(messages)
    assert len(instructions) == 1
    assert "Part1 Part2" in instructions[0]["synopsis"]
