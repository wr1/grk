"""Tests for utility functions in grk.utils."""

from rich.console import Console
from grk.utils import print_instruction_tree, build_instructions_from_messages
from xai_sdk.chat import system, user, assistant


def test_build_instructions_from_messages():
    """Test building instructions from messages, skipping empty."""
    messages = [
        system("System message"),
        user("User message", name="User1"),
        assistant("Assistant message"),
        user(""),  # Empty, should be skipped
    ]
    instructions = build_instructions_from_messages(messages)
    assert len(instructions) == 3
    assert instructions[0]["role"] == "system"
    assert instructions[0]["synopsis"] == "System message"
    assert instructions[1]["role"] == "user"
    assert instructions[1]["name"] == "User1"
    assert instructions[1]["synopsis"] == "User message"
    assert instructions[2]["role"] == "assistant"
    assert instructions[2]["synopsis"] == "Assistant message"


def test_print_instruction_tree(capsys):
    """Test printing instruction tree with colors and filtering."""
    console = Console(file=None, force_terminal=True)
    instructions = [
        {"role": "system", "name": "Sys1", "synopsis": "System msg"},
        {"role": "user", "name": "User1", "synopsis": "User msg"},
        {"role": "assistant", "synopsis": ""},  # Empty, skipped
        {"role": "assistant", "synopsis": "Assistant msg"},
    ]
    print_instruction_tree(console, instructions)
    captured = capsys.readouterr()
    assert "[cyan]system[/cyan] (Sys1): System msg" in captured.out
    assert "[cyan]user[/cyan] (User1): User msg" in captured.out
    assert "[cyan]assistant[/cyan]: Assistant msg" in captured.out
    assert captured.out.count("\n") == 3  # Title + 3 lines


def test_print_instruction_tree_no_instructions(capsys):
    """Test printing when no instructions after filtering."""
    console = Console(file=None, force_terminal=True)
    print_instruction_tree(console, [])
    captured = capsys.readouterr()
    assert "[yellow]No instructions.[/yellow]" in captured.out
