"""Tests for config_handler module."""

from pathlib import Path
from ruamel.yaml import YAML
from grk.config.config_handler import list_configs


def test_list_configs_no_file(tmp_path, monkeypatch, caplog):
    """Test list_configs when no .grkrc exists."""
    monkeypatch.chdir(tmp_path)
    with caplog.at_level("INFO"):
        list_configs()
    assert "No .grkrc file found" in caplog.text


def test_list_configs_with_profiles(tmp_path, monkeypatch, capsys):
    """Test list_configs with profiles in .grkrc."""
    monkeypatch.chdir(tmp_path)
    config_data = {"profiles": {"default": {"model": "grok-4-fast"}}}
    yaml = YAML()
    with Path(".grkrc").open("w") as f:
        yaml.dump(config_data, f)
    list_configs()
    captured = capsys.readouterr()
    assert "profiles:" in captured.out
    assert "default:" in captured.out


def test_list_configs_no_profiles(tmp_path, monkeypatch, caplog):
    """Test list_configs with no profiles."""
    monkeypatch.chdir(tmp_path)
    Path(".grkrc").write_text("{}")
    with caplog.at_level("INFO"):
        list_configs()
    assert "No profiles defined" in caplog.text


def test_list_configs_invalid_yaml(tmp_path, monkeypatch, caplog):
    """Test list_configs with invalid YAML."""
    monkeypatch.chdir(tmp_path)
    Path(".grkrc").write_text("invalid yaml without colon")
    with caplog.at_level("WARNING", logger="grk"):
        list_configs()
    assert "Failed to load .grkrc" in caplog.text
