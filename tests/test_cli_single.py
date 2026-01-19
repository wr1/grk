"""Tests for CLI single commands."""

import pytest
from pathlib import Path
from io import StringIO
from grk.cli.cli import main
import sys
import os


@pytest.fixture
def capture_output():
    """Fixture to capture stdout and stderr."""

    def _capture(args, env=None):
        old_argv = sys.argv
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        old_env = os.environ.copy()
        sys.argv = ["grk"] + args
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        if env:
            os.environ.update(env)
        exit_code = 0
        try:
            main()
        except SystemExit as e:
            exit_code = e.code or 0
        except Exception as e:
            exit_code = 1
            sys.stderr.write(str(e) + "\n")
        finally:
            output = sys.stdout.getvalue()
            error = sys.stderr.getvalue()
            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            os.environ.clear()
            os.environ.update(old_env)
        return type("Result", (), {"exit_code": exit_code, "output": output + error})

    return _capture


def test_run_command_no_api_key(capture_output, tmp_path, monkeypatch):
    """Test run command without API key set."""
    monkeypatch.chdir(tmp_path)
    Path("input.txt").write_text("Test content")
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    result = capture_output(["single", "run", "input.txt", "Test prompt"])
    assert result.exit_code != 0
    assert "API key is required" in result.output


def test_run_command_file_not_found(capture_output, tmp_path, monkeypatch):
    """Test run command with non-existent input file."""
    monkeypatch.chdir(tmp_path)
    result = capture_output(
        ["single", "run", "nonexistent.txt", "Test prompt"],
        env={"XAI_API_KEY": "dummy_key"},
    )
    assert result.exit_code != 0
    assert "Invalid file" in result.output


@pytest.mark.parametrize(
    "profile",
    ["default", "py", "doc"],
)
def test_run_command_with_profile(
    capture_output, tmp_path, monkeypatch, profile, mocker, caplog
):
    """Test run command with different profiles."""
    monkeypatch.chdir(tmp_path)
    Path("input.txt").write_text("Test content")

    # Initialize config to have profiles
    capture_output(["config", "init"])

    # Set up mock for API call
    mock_call_grok = mocker.patch("grk.core.runner.call_grok", return_value=f"Response for {profile}")

    cmd = ["single", "run", "input.txt", "Test prompt"]
    if profile != "default":
        cmd.extend(["--profile", profile])
    with caplog.at_level("INFO"):
        result = capture_output(cmd, env={"XAI_API_KEY": "dummy_key"})
    assert result.exit_code == 0

    # Check if API was called with correct model based on profile
    expected_models = {
        "default": "grok-code-fast-1",
        "py": "grok-code-fast-1",
        "doc": "grok-4-1-fast",
    }
    called_model = mock_call_grok.call_args[0][1]
    assert called_model == expected_models.get(profile, "grok-4-fast")
