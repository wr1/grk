import pytest
import click
from click.testing import CliRunner
from pathlib import Path
from grk.cli import main, call_grok
import requests

@pytest.fixture
def runner():
    """Fixture for invoking CLI commands."""
    return CliRunner()

def test_main_help(runner):
    """Test main CLI help command."""
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert 'CLI tool to interact with Grok LLM.' in result.output

def test_init_command(runner, tmp_path, monkeypatch):
    """Test init command to create default .grkrc file."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(main, ['init'])
    assert result.exit_code == 0
    assert Path('.grkrc').exists()
    assert 'Default .grkrc with profiles created successfully' in result.output

def test_run_command_no_api_key(runner, tmp_path, monkeypatch):
    """Test run command without API key set."""
    monkeypatch.chdir(tmp_path)
    Path('input.txt').write_text('Test content')
    monkeypatch.delenv('XAI_API_KEY', raising=False)
    result = runner.invoke(main, ['run', 'input.txt', 'Test prompt'])
    assert result.exit_code != 0
    assert 'API key is required' in result.output

def test_run_command_file_not_found(runner, tmp_path, monkeypatch):
    """Test run command with non-existent input file."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('XAI_API_KEY', 'dummy_key')
    result = runner.invoke(main, ['run', 'nonexistent.txt', 'Test prompt'])
    assert result.exit_code != 0
    assert 'does not exist' in result.output.lower()  # Click error for non-existent path

@pytest.mark.parametrize("profile", ["default", "py", "doc"])
def test_run_command_with_profile(runner, tmp_path, monkeypatch, profile, mocker):
    """Test run command with different profiles."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('XAI_API_KEY', 'dummy_key')
    Path('input.txt').write_text('Test content')

    mock_response = mocker.patch('requests.post')
    mock_response.return_value.status_code = 200
    mock_response.return_value.json.return_value = {
        "choices": [{"message": {"content": f"Response for {profile}"}}]
    }

    cmd = ['run', 'input.txt', 'Test prompt']
    if profile != "default":
        cmd.extend(['-p', profile])
    result = runner.invoke(main, cmd)
    assert result.exit_code == 0
    assert "Running grk with the following settings:" in result.output
    assert f"  Profile: {profile}" in result.output
    assert Path('output.txt').exists()

def test_call_grok_api_failure(runner, tmp_path, monkeypatch, mocker):
    """Test API call failure handling in call_grok."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('XAI_API_KEY', 'dummy_key')

    mock_response = mocker.patch('requests.post')
    mock_response.side_effect = requests.exceptions.RequestException("API error")

    with pytest.raises(click.ClickException) as exc_info:
        call_grok("Test content", "Test prompt", "grok-3", "dummy_key", "python-programmer")
    assert "API request failed" in str(exc_info.value)
