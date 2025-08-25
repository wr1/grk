"""Tests for Grok CLI commands."""

import pytest
from unittest.mock import patch
import json
from pathlib import Path
from io import StringIO
from grk.cli import main
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
        sys.argv = ['grk'] + args
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
        return type('Result', (), {'exit_code': exit_code, 'output': output + error})
    return _capture


def test_main_help(capture_output):
    """Test main CLI help command."""
    result = capture_output(["--help"])
    assert result.exit_code == 0
    assert "grk" in result.output
    assert "init" in result.output
    assert "list" in result.output
    assert "run" in result.output
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


def test_init_command(capture_output, tmp_path, monkeypatch):
    """Test init command to create default .grkrc file."""
    monkeypatch.chdir(tmp_path)
    result = capture_output(["init"])
    assert result.exit_code == 0
    assert Path(".grkrc").exists()


def test_run_command_no_api_key(capture_output, tmp_path, monkeypatch):
    """Test run command without API key set."""
    monkeypatch.chdir(tmp_path)
    Path("input.txt").write_text("Test content")
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    result = capture_output(["run", "input.txt", "Test prompt"])
    assert result.exit_code != 0
    assert "API key is required" in result.output


def test_run_command_file_not_found(capture_output, tmp_path, monkeypatch):
    """Test run command with non-existent input file."""
    monkeypatch.chdir(tmp_path)
    result = capture_output(["run", "nonexistent.txt", "Test prompt"], env={"XAI_API_KEY": "dummy_key"})
    assert result.exit_code != 0
    assert "Invalid file" in result.output


@pytest.mark.parametrize(
    "profile",
    ["default", "py", "doc"],
)
def test_run_command_with_profile(capture_output, tmp_path, monkeypatch, profile, mocker):
    """Test run command with different profiles."""
    monkeypatch.chdir(tmp_path)
    Path("input.txt").write_text("Test content")

    # Initialize config to have profiles
    capture_output(["init"])

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
        cmd.extend(["--profile", profile])
    result = capture_output(cmd, env={"XAI_API_KEY": "dummy_key"})
    assert result.exit_code == 0
    assert "Running grk with the following settings:" in result.output

    # Check if API was called with correct model based on profile
    expected_models = {"default": "grok-4", "py": "grok-4", "doc": "grok-4"}
    called_model = mock_client.chat.create.call_args.kwargs["model"]
    assert called_model == expected_models.get(profile, "grok-4")

    # Check output files
    assert Path("output.json").exists()  # Adjusted to match default


def test_session_up_command(capture_output, tmp_path, monkeypatch, mocker):
    """Test session up command (stubbed for process start)."""
    monkeypatch.chdir(tmp_path)
    Path("initial.json").write_text('{"files": []}')
    mock_popen = mocker.patch("subprocess.Popen")
    mock_popen.return_value.pid = 12345  # Mock pid
    result = capture_output(["session", "up", "initial.json"], env={"XAI_API_KEY": "dummy_key"})
    assert result.exit_code == 0
    assert "Session started with PID 12345" in result.output
    assert Path(".grk_session.pid").exists()
    assert Path(".grk_session.json").exists()


def test_session_msg_postprocessing(capture_output, tmp_path, monkeypatch, mocker):
    """Test session msg command with postprocessing of malformed responses."""
    monkeypatch.chdir(tmp_path)
    Path("initial.json").write_text('{"files": []}')
    Path(".grk_session.pid").write_text("12345")
    Path(".grk_session.json").write_text(
        json.dumps({"profile": "default", "initial_file": "initial.json", "pid": 12345})
    )
    Path(".grk_session.port").write_text("12345")

    # Mock socket for testing postprocessing
    mock_socket = mocker.Mock()
    mock_socket.connect = mocker.Mock()
    mock_socket.send = mocker.Mock()

    # Mock response for 'list' command
    list_resp = {"files": [], "instructions": []}
    list_resp_json = json.dumps(list_resp)
    list_length = len(list_resp_json)
    list_length_bytes = list_length.to_bytes(4, "big")
    list_data_bytes = list_resp_json.encode()

    # Mock response for 'query' command
    resp = {"summary": "= No changes detected.", "message": "Here's the update:"}
    resp_json = json.dumps(resp)
    length = len(resp_json)
    length_bytes = length.to_bytes(4, "big")
    data_bytes = resp_json.encode()

    mock_socket.recv.side_effect = [
        list_length_bytes,
        list_data_bytes,
        length_bytes,
        data_bytes,
    ]
    mocker.patch("socket.socket", return_value=mock_socket)

    result = capture_output(["session", "msg", "Test prompt", "-o", "__temp.json"])
    assert result.exit_code == 0
    assert "Message from Grok: Here's the update:" in result.output
    assert "Summary:" in result.output
    assert "= No changes detected." in result.output


def test_session_new_command(capture_output, tmp_path, monkeypatch, mocker):
    """Test session new command to renew instruction stack."""
    monkeypatch.chdir(tmp_path)
    Path(".grk_session.pid").write_text("12345")
    Path(".grk_session.port").write_text("12345")
    Path("new.json").write_text('{"instructions": [], "files": []}')

    mock_socket = mocker.Mock()
    mock_socket.connect = mocker.Mock()
    mock_socket.send = mocker.Mock()

    resp = {"message": "Instruction stack renewed."}
    resp_json = json.dumps(resp)
    length = len(resp_json)
    length_bytes = length.to_bytes(4, "big")
    data_bytes = resp_json.encode()

    mock_socket.recv.side_effect = [length_bytes, data_bytes]
    mocker.patch("socket.socket", return_value=mock_socket)

    result = capture_output(["session", "new", "new.json"])
    assert result.exit_code == 0
    assert "Success: Instruction stack renewed." in result.output


@pytest.mark.parametrize(
    "raw_response, expected_cleaned, expected_message",
    [
        ('[{"path": "file.txt"}]', '{"files": [{"path": "file.txt"}]}', ""),
        (
            'Here\'s the update: ```json\n[{"path": "file.txt"}]\n```',
            '{"files": [{"path": "file.txt"}]}',
            "Here's the update:",
        ),
        (
            'Explanatory text {"files": [{"path": "file.txt"}]}',
            '{"files": [{"path": "file.txt"}]}',
            "Explanatory text",
        ),
        ("Invalid response without JSON", "", "Invalid response without JSON"),
    ],
)
def test_postprocess_response(raw_response, expected_cleaned, expected_message):
    """Test postprocess_response function."""
    from grk.core.session import postprocess_response

    cleaned, message = postprocess_response(raw_response)
    assert cleaned.replace("\n", "") == expected_cleaned.replace(
        "\n", ""
    )  # Ignore formatting
    assert message == expected_message

