"""CLI commands for interacting with Grok LLM."""

import pytest
from click.testing import CliRunner
from pathlib import Path
from grk.cli import main


@pytest.fixture
def runner():
    """Fixture for invoking CLI commands."""
    return CliRunner()


def test_main_help(runner):
    """Test main CLI help command."""
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "CLI tool to interact with Grok LLM." in result.output


def test_init_command(runner, tmp_path, monkeypatch):
    """Test init command to create default .grkrc file."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(main, ["init"])
    assert result.exit_code == 0
    assert Path(".grkrc").exists()
    assert "Default .grkrc with profiles created successfully" in result.output


def test_run_command_no_api_key(runner, tmp_path, monkeypatch):
    """Test run command without API key set."""
    monkeypatch.chdir(tmp_path)
    Path("input.txt").write_text("Test content")
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    result = runner.invoke(main, ["run", "input.txt", "Test prompt"])
    assert result.exit_code != 0
    assert "API key is required" in result.output


def test_run_command_file_not_found(runner, tmp_path, monkeypatch):
    """Test run command with non-existent input file."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("XAI_API_KEY", "dummy_key")
    result = runner.invoke(main, ["run", "nonexistent.txt", "Test prompt"])
    assert result.exit_code != 0
    assert "does not exist" in result.output


@pytest.mark.parametrize("profile", ["default", "py", "doc"])
def test_run_command_with_profile(runner, tmp_path, monkeypatch, profile, mocker):
    """Test run command with different profiles."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("XAI_API_KEY", "dummy_key")
    Path("input.txt").write_text("Test content")

    # Initialize config to have profiles
    init_result = runner.invoke(main, ["init"])
    assert init_result.exit_code == 0

    # Set up mock for API call
    mock_client = mocker.Mock()
    mock_client.chat = mocker.Mock()
    mock_chat = mocker.Mock()
    mock_sample = mocker.Mock()
    mock_sample.content = f"Response for {profile}"
    mock_chat.sample.return_value = mock_sample
    mock_client.chat.create.return_value = mock_chat
    mocker.patch("grk.api.Client", return_value=mock_client)

    cmd = ["run", "input.txt", "Test prompt"]
    if profile != "default":
        cmd.extend(["-p", profile])
    result = runner.invoke(main, cmd)
    assert result.exit_code == 0
    assert "Running grk with the following settings:" in result.output

    # Check if API was called with correct model based on profile
    expected_models = {"default": "grok-4", "py": "grok-3-mini-fast", "doc": "grok-3"}
    called_model = mock_client.chat.create.call_args.kwargs["model"]
    assert called_model == expected_models[profile]

    # Check output files
    assert Path("output.txt").exists()
    assert Path(f"grk_{profile}_output.json").exists()
