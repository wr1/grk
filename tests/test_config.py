from pathlib import Path
from ruamel.yaml import YAML
from grk.config import load_config, create_default_config
from grk.models import ProfileConfig  # Import for type checking

def test_load_config_no_file(tmp_path, monkeypatch):
    """Test load_config when .grkrc file does not exist."""
    monkeypatch.chdir(tmp_path)
    result = load_config()
    assert isinstance(result, ProfileConfig)
    assert result.model is None  # Empty ProfileConfig

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
    assert isinstance(result, ProfileConfig)
    assert result.model == "grok-3"
    assert result.role == "python-programmer"

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
    assert isinstance(result, ProfileConfig)
    assert result.model == "grok-3-custom"

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
    assert isinstance(result, ProfileConfig)
    assert result.model is None

def test_load_config_invalid_yaml(tmp_path, monkeypatch, capsys):
    """Test load_config with invalid YAML content."""
    monkeypatch.chdir(tmp_path)
    Path(".grkrc").write_text("invalid: yaml: content: : :")
    
    result = load_config()
    captured = capsys.readouterr()
    assert "Warning: Failed to load .grkrc profile 'default'" in captured.out
    assert isinstance(result, ProfileConfig)
    assert result.model is None  # Returns empty ProfileConfig on failure

def test_create_default_config(tmp_path, monkeypatch, capsys):
    """Test create_default_config creates default .grkrc file."""
    monkeypatch.chdir(tmp_path)
    create_default_config()
    assert Path('.grkrc').exists()
    captured = capsys.readouterr()
    assert "Default .grkrc with profiles created successfully" in captured.out
