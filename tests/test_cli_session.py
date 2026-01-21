"""Tests for CLI session commands."""

import pytest
import json
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


def test_session_up_command(capture_output, tmp_path, monkeypatch, mocker, caplog):
    """Test session up command (stubbed for process start)."""
    monkeypatch.chdir(tmp_path)
    Path("initial.json").write_text('{"files": []}')
    mock_popen = mocker.patch("subprocess.Popen")
    mock_popen.return_value.pid = 12345  # Mock pid
    with caplog.at_level("INFO"):
        result = capture_output(
            ["session", "up", "initial.json"], env={"XAI_API_KEY": "dummy_key"}
        )
    assert result.exit_code == 0
    assert "Session started with PID 12345" in caplog.text
    assert Path(".grk_session.pid").exists()
    assert Path(".grk_session.json").exists()


def test_session_up_invalid_file(capture_output, tmp_path, monkeypatch):
    """Test session up command with invalid file."""
    monkeypatch.chdir(tmp_path)
    result = capture_output(
        ["session", "up", "nonexistent.json"], env={"XAI_API_KEY": "dummy_key"}
    )
    assert result.exit_code != 0
    assert "Invalid file" in result.output


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
    mocker.patch("select.select", return_value=([mock_socket], [], []))

    result = capture_output(["session", "msg", "Test prompt", "-o", "__temp.json"])
    assert result.exit_code == 0
    assert "Message from Grok: Here's the update:" in result.output
    assert "Summary:" in result.output
    assert "= No changes detected." in result.output


def test_session_msg_invalid_input_file(capture_output, tmp_path, monkeypatch):
    """Test session msg command with invalid input file."""
    monkeypatch.chdir(tmp_path)
    Path("initial.json").write_text('{"files": []}')
    Path(".grk_session.pid").write_text("12345")
    Path(".grk_session.json").write_text(
        json.dumps({"profile": "default", "initial_file": "initial.json", "pid": 12345})
    )
    Path(".grk_session.port").write_text("12345")
    result = capture_output(["session", "msg", "Test prompt", "-i", "nonexistent.txt"])
    assert result.exit_code != 0
    assert "Invalid input file" in result.output


def test_session_msg_no_session(capture_output, tmp_path, monkeypatch):
    """Test session msg command with no session running."""
    monkeypatch.chdir(tmp_path)
    result = capture_output(["session", "msg", "Test prompt"])
    assert result.exit_code != 0
    assert "No session running" in result.output


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
    mocker.patch("select.select", return_value=([mock_socket], [], []))

    result = capture_output(["session", "new", "new.json"])
    assert result.exit_code == 0
    assert "Success: Instruction stack renewed." in result.output


def test_session_new_no_session(capture_output, tmp_path, monkeypatch):
    """Test session new command with no session running."""
    monkeypatch.chdir(tmp_path)
    Path("file.json").write_text('{"instructions": [], "files": []}')
    result = capture_output(["session", "new", "file.json"])
    assert result.exit_code != 0
    assert "No session running" in result.output


def test_session_down_command(capture_output, tmp_path, monkeypatch, mocker):
    """Test session down command."""
    monkeypatch.chdir(tmp_path)
    Path(".grk_session.pid").write_text("12345")
    Path(".grk_session.port").write_text("12345")

    mock_socket = mocker.Mock()
    mock_socket.connect = mocker.Mock()
    mock_socket.send = mocker.Mock()

    resp = "Shutting down"
    length = len(resp)
    length_bytes = length.to_bytes(4, "big")
    data_bytes = resp.encode()

    mock_socket.recv.side_effect = [length_bytes, data_bytes]
    mocker.patch("socket.socket", return_value=mock_socket)
    mocker.patch("select.select", return_value=([mock_socket], [], []))
    mocker.patch("os.kill")

    result = capture_output(["session", "down"])
    assert result.exit_code == 0
    assert not Path(".grk_session.pid").exists()
    assert not Path(".grk_session.port").exists()


def test_session_down_no_session(capture_output, tmp_path, monkeypatch):
    """Test session down command with no session running."""
    monkeypatch.chdir(tmp_path)
    result = capture_output(["session", "down"])
    assert result.exit_code != 0
    assert "No session running" in result.output


def test_session_list_command(capture_output, tmp_path, monkeypatch, mocker):
    """Test session list command."""
    monkeypatch.chdir(tmp_path)
    Path(".grk_session.pid").write_text("12345")
    Path(".grk_session.port").write_text("12345")
    Path(".grk_session.json").write_text(
        json.dumps({"profile": "default", "initial_file": "initial.json"})
    )

    mock_socket = mocker.Mock()
    mock_socket.connect = mocker.Mock()
    mock_socket.send = mocker.Mock()

    resp = {
        "files": ["file1.txt"],
        "instructions": [{"role": "system", "synopsis": "test"}],
    }
    resp_json = json.dumps(resp)
    length = len(resp_json)
    length_bytes = length.to_bytes(4, "big")
    data_bytes = resp_json.encode()

    mock_socket.recv.side_effect = [length_bytes, data_bytes]
    mocker.patch("socket.socket", return_value=mock_socket)
    mocker.patch("select.select", return_value=([mock_socket], [], []))

    result = capture_output(["session", "list"])
    assert result.exit_code == 0
    assert "Session Details:" in result.output
    assert "file1.txt" in result.output
    assert "system: test" in result.output


def test_session_list_no_session(capture_output, tmp_path, monkeypatch):
    """Test session list command with no session running."""
    monkeypatch.chdir(tmp_path)
    result = capture_output(["session", "list"])
    assert result.exit_code != 0
    assert "No session running" in result.output


def test_session_up_cleanup_stale_pid(
    capture_output, tmp_path, monkeypatch, mocker, caplog
):
    """Test session up command with stale PID cleanup."""
    monkeypatch.chdir(tmp_path)
    Path("initial.json").write_text('{"files": []}')
    Path(".grk_session.pid").write_text("999999")  # Invalid pid to force OSError
    mocker.patch("os.kill", side_effect=OSError("Process not found"))
    mock_popen = mocker.patch("subprocess.Popen")
    mock_popen.return_value.pid = 12345
    with caplog.at_level("INFO"):
        result = capture_output(
            ["session", "up", "initial.json"], env={"XAI_API_KEY": "dummy_key", "PYTEST_CURRENT_TEST": "test"}
        )
    assert result.exit_code == 0
    assert "Session started with PID 12345" in caplog.text
    assert Path(".grk_session.pid").exists()
    assert Path(".grk_session.json").exists()
