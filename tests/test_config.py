from pathlib import Path
from ruamel.yaml import YAML
from grk.config import load_config

def test_load_config_no_file(tmp_path, monkeypatch):
    """Test load_config when .grkrc file does not exist."""
    monkeypatch.chdir(tmp_path)
    result = load_config()
    assert result == {}, "Should return empty dict if no config file exists"

def test_load_config_default_profile(tmp_path, monkeypatch):
    """Test load_config with a valid .grkrc file for default profile."""
    monkeypatch.chdir(tmp_path)
    config_data = {
        "profiles": {
            "default": {
                "model": "grok-3",
                "role": "python-programmer",
                "output": "output.txt"
            }
        }
    }
    yaml = YAML()
    with Path(".grkrc").open("w") as f:
        yaml.dump(config_data, f)
    
    result = load_config()
    assert result == config_data["profiles"]["default"], "Should load default profile from .grkrc"

def test_load_config_custom_profile(tmp_path, monkeypatch):
    """Test load_config with a valid .grkrc file for a custom profile."""
    monkeypatch.chdir(tmp_path)
    config_data = {
        "profiles": {
            "custom": {
                "model": "grok-3-custom",
                "role": "documentation-specialist",
                "output": "custom_output.txt"
            }
        }
    }
    yaml = YAML()
    with Path(".grkrc").open("w") as f:
        yaml.dump(config_data, f)
    
    result = load_config(profile="custom")
    assert result == config_data["profiles"]["custom"], "Should load custom profile from .grkrc"

def test_load_config_nonexistent_profile(tmp_path, monkeypatch):
    """Test load_config when the specified profile does not exist."""
    monkeypatch.chdir(tmp_path)
    config_data = {
        "profiles": {
            "default": {
                "model": "grok-3",
                "role": "python-programmer"
            }
        }
    }
    yaml = YAML()
    with Path(".grkrc").open("w") as f:
        yaml.dump(config_data, f)
    
    result = load_config(profile="nonexistent")
    assert result == {}, "Should return empty dict for nonexistent profile"

def test_load_config_invalid_yaml(tmp_path, monkeypatch, capsys):
    """Test load_config with invalid YAML content."""
    monkeypatch.chdir(tmp_path)
    Path(".grkrc").write_text("invalid: yaml: content: : :")
    
    result = load_config()
    captured = capsys.readouterr()
    assert "Warning: Failed to load .grkrc profile 'default'" in captured.out, "Should print warning for invalid YAML"
    assert result == {}, "Should return empty dict for invalid YAML"
