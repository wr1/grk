"""Tests for core.session module."""

from grk.core.session import (
    apply_cfold_changes,
    postprocess_response,
    load_cached_codebase,
    save_cached_codebase,
    recv_full,
)
from pathlib import Path
import pytest
from unittest.mock import Mock


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


def test_postprocess_response_no_json():
    """Test postprocess_response with no JSON."""
    response = "Just text"
    cleaned, message = postprocess_response(response)
    assert cleaned == ""
    assert message == "Just text"


def test_postprocess_response_embedded_json():
    """Test postprocess_response with embedded JSON."""
    response = 'Intro [{"path": "file.txt"}] end'
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
