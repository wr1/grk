"""Tests for core.session module."""

from grk.core.session import apply_cfold_changes, postprocess_response, load_cached_codebase, save_cached_codebase, recv_full, send_response, daemon_process
from pathlib import Path
import socket
import pytest
from unittest.mock import patch, Mock
import json
import time
from xai_sdk import Client
from xai_sdk.chat import system, user, assistant
from grk.models import ProfileConfig
from grk.utils import GrkException


def test_apply_cfold_changes():
    """Test applying cfold changes to existing codebase."""
    existing = [
        {"path": "file1.txt", "content": "old"},
        {"path": "file2.txt", "content": "keep"},
    ]
    changes = [
        {"path": "file1.txt", "content": "new"},
        {"path": "file3.txt", "content": "added"},
        {"path": "file2.txt", "delete": True},
        {"path": "../invalid.txt", "content": "skip"},  # Invalid path
    ]
    updated = apply_cfold_changes(existing, changes)
    assert len(updated) == 2
    assert updated[0]["path"] == "file1.txt"
    assert updated[0]["content"] == "new"
    assert updated[1]["path"] == "file3.txt"
    assert "file2.txt" not in [f["path"] for f in updated]


def test_apply_cfold_changes_invalid_path():
    """Test applying cfold changes with invalid paths."""
    existing = [{"path": "file.txt", "content": "old"}]
    changes = [
        {"path": "../invalid.txt", "content": "new"},
        {"path": "/root/invalid.txt", "content": "new2"},
    ]
    updated = apply_cfold_changes(existing, changes)
    assert updated == existing  # No changes applied


def test_postprocess_response_no_json():
    """Test postprocess_response with no JSON."""
    response = "Just text"
    cleaned, message = postprocess_response(response)
    assert cleaned == ""
    assert message == "Just text"


def test_postprocess_response_embedded_json():
    """Test postprocess_response with embedded JSON."""
    response = "Intro [{\"path\": \"file.txt\"}] end"
    cleaned, message = postprocess_response(response)
    assert cleaned == '{"files": [{"path": "file.txt"}]}'
    assert message == "Intro  end"


def test_load_cached_codebase_no_file(tmp_path, monkeypatch):
    """Test load_cached_codebase with no cache file."""
    monkeypatch.chdir(tmp_path)
    assert load_cached_codebase() == []


def test_load_cached_codebase_corrupted(tmp_path, monkeypatch, caplog):
    """Test load_cached_codebase with corrupted file."""
    monkeypatch.chdir(tmp_path)
    Path(".grk_cache.json").write_text("invalid json")
    with caplog.at_level("WARNING"):
        assert load_cached_codebase() == []
    assert "Cache file is corrupted" in caplog.text


def test_save_cached_codebase(tmp_path, monkeypatch, caplog):
    """Test save_cached_codebase."""
    monkeypatch.chdir(tmp_path)
    codebase = [{"path": "file.txt", "content": "content"}]
    save_cached_codebase(codebase)
    assert Path(".grk_cache.json").exists()
    assert "file.txt" in Path(".grk_cache.json").read_text()


def test_recv_full():
    """Test recv_full receives exact size."""
    mock_conn = Mock()
    mock_conn.recv.side_effect = [b"ab", b"c"]
    assert recv_full(mock_conn, 3) == b"abc"


def test_recv_full_incomplete():
    """Test recv_full raises on incomplete data."""
    mock_conn = Mock()
    mock_conn.recv.side_effect = [b"ab", b""]
    with pytest.raises(ValueError):
        recv_full(mock_conn, 3)


def test_send_response():
    """Test send_response sends with length prefix."""
    mock_conn = Mock()
    send_response(mock_conn, {"key": "value"})
    sent = mock_conn.send.call_args[0][0]
    length = int.from_bytes(sent[:4], "big")
    data = sent[4:]
    assert json.loads(data) == {"key": "value"}
    assert length == len(data)

@patch("grk.core.session.Client")
@patch("grk.core.session.socket")
@patch("grk.core.session.Path")
@patch("grk.core.session.load_brief")
def test_daemon_process(mock_load_brief, mock_path_class, mock_socket_module, mock_client_class, tmp_path, monkeypatch):
    """Test daemon_process with mocks."""
    mock_load_brief.return_value = None  # Skip brief loading
    monkeypatch.chdir(tmp_path)
    initial_file = "initial.json"
    # Setup mock for initial file read
    mock_initial_path = Mock()
    mock_initial_path.read_text.return_value = '{"files": [], "instructions": []}'
    # Setup mock for port file
    mock_port_path = Mock()
    mock_port_path.write_text = Mock()
    # Mock Path calls
    def path_side_effect(path):
        if path == initial_file:
            return mock_initial_path
        elif path == ".grk_session.port":
            return mock_port_path
        else:
            return Mock()  # For other paths like cache
    mock_path_class.side_effect = path_side_effect

    config = ProfileConfig()
    api_key = "test_key"

    mock_server = Mock()
    mock_socket_module.socket.return_value = mock_server
    mock_server.getsockname.return_value = ("127.0.0.1", 12345)
    mock_conn = Mock()
    mock_server.accept.return_value = (mock_conn, ("addr"))

    # Mock recv_full for length and data
    def mock_recv_full(conn, size):
        if size == 4:
            return (18).to_bytes(4, "big")  # Length for '{"cmd": "down"}'
        elif size == 18:
            return b'{"cmd": "down"}'
        return b""

    with patch("grk.core.session.recv_full", side_effect=mock_recv_full):
        daemon_process(initial_file, config, api_key)

    assert mock_server.bind.called
    assert mock_server.listen.called
    assert mock_conn.close.called
    assert mock_port_path.write_text.called
    assert mock_server.close.called
