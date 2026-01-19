"""Tests for CLI config commands."""

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


def test_init_command(capture_output, tmp_path, monkeypatch, caplog):
    """Test init command to create default .grkrc file."""
    monkeypatch.chdir(tmp_path)
    with caplog.at_level("INFO"):
        result = capture_output(["config", "init"])
    assert result.exit_code == 0
    assert Path(".grkrc").exists()
    assert "Default .grkrc with profiles created successfully." in caplog.text


def test_init_command_with_existing_config(
    capture_output, tmp_path, monkeypatch, caplog
):
    """Test init command with existing .grkrc file."""
    monkeypatch.chdir(tmp_path)
    Path(".grkrc").write_text("profiles:\n  default:\n    model: grok-3\n")
    with caplog.at_level("INFO"):
        result = capture_output(["config", "init"])
    assert result.exit_code == 0
    assert "Profile 'default' differs from default" in caplog.text


def test_init_command_with_existing_brief(
    capture_output, tmp_path, monkeypatch, caplog
):
    """Test init command with existing brief configuration."""
    monkeypatch.chdir(tmp_path)
    Path(".grkrc").write_text("brief:\n  file: old_brief.txt\n  role: user\n")
    with caplog.at_level("INFO"):
        result = capture_output(["config", "init"])
    assert result.exit_code == 0
    assert "Brief differs from default, saved old as 'brief_old'." in caplog.text
