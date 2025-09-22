"""Tests for runner module."""

import pytest
from grk.core.runner import run_grok
from grk.config.config import ProfileConfig
from grk.utils.utils import GrkException
from pathlib import Path
import json
from unittest.mock import patch


def test_run_grok_invalid_file(tmp_path, monkeypatch):
    """Test run_grok with invalid input file."""
    monkeypatch.chdir(tmp_path)
    config = ProfileConfig()
    with pytest.raises(GrkException) as exc:
        run_grok("nonexistent.txt", "prompt", config, "key")
    assert "Failed to read file" in str(exc.value)


@patch("grk.core.runner.call_grok")
def test_run_grok_success(mock_call, tmp_path, monkeypatch):
    """Test successful run_grok execution."""
    monkeypatch.chdir(tmp_path)
    Path("input.json").write_text('{"files": []}')
    mock_call.return_value = '{"files": [{"path": "new.txt", "content": "content"}]}'
    config = ProfileConfig(output="output.json")
    run_grok("input.json", "prompt", config, "key")
    assert Path("output.json").exists()
    data = json.loads(Path("output.json").read_text())
    assert "files" in data
    assert len(data["files"]) == 1


@patch("grk.core.runner.call_grok")
def test_run_grok_non_json_input(mock_call, tmp_path, monkeypatch):
    """Test run_grok with non-JSON input file."""
    monkeypatch.chdir(tmp_path)
    Path("input.txt").write_text("Non-JSON content")
    mock_call.return_value = "Response text"
    config = ProfileConfig(output="output.txt")
    run_grok("input.txt", "prompt", config, "key")
    assert Path("output.txt").read_text() == "Response text"
