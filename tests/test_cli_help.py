"""Tests for CLI help commands."""

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


def test_main_help(capture_output):
    """Test main CLI help command."""
    result = capture_output(["--help"])
    assert result.exit_code == 0
    assert "grk" in result.output
    assert "config" in result.output
    assert "single" in result.output
    assert "session" in result.output


def test_session_help(capture_output):
    """Test session subgroup help."""
    result = capture_output(["session", "--help"])
    assert result.exit_code == 0
    assert "up" in result.output
    assert "new" in result.output
    assert "msg" in result.output
    assert "list" in result.output
    assert "down" in result.output


def test_config_help(capture_output):
    """Test config subgroup help."""
    result = capture_output(["config", "--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "list" in result.output


def test_single_help(capture_output):
    """Test single subgroup help."""
    result = capture_output(["single", "--help"])
    assert result.exit_code == 0
    assert "run" in result.output
