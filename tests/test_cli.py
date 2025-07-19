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
    result = runner.invoke(main, ['run', '--file', 'input.txt', '--prompt', 'Test prompt'])
    assert result.exit_code != 0
    assert 'API key is required' in result.output

def test_run_command_file_not_found(runner, tmp_path, monkeypatch):
    """Test run command with non-existent input file."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('XAI_API_KEY', 'dummy_key')
    result = runner.invoke(main, ['run', '--file', 'nonexistent.txt', '--prompt', 'Test prompt'])
    assert result.exit_code != 0
    assert 'Failed to read file' in result.output

@pytest.mark.parametrize("profile", ["default", "py", "doc"])
def test_run_command_with_profile(runner, tmp_path, monkeypatch, profile, mocker):
    """Test run command with different profiles."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('XAI_API_KEY', 'dummy_key')
    Path('input.txt').write_text('Test content')

    mock_post = mocker.patch('requests.post')
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": f"Response for {profile}"}}]
    }
    mock_post.return_value = mock_response

    cmd = ['run', '--file', 'input.txt', '--prompt', 'Test prompt']
    if profile != "default":
        cmd.extend(['-p', profile])
    result = runner.invoke(main, cmd)
    assert result.exit_code == 0
    assert "Running grk with the following settings:" in result.output
    assert Path('output.txt').exists()
