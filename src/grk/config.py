from pathlib import Path
from ruamel.yaml import YAML


def load_config(profile: str = "default") -> dict:
    """Load specified profile from .grkrc YAML config file."""
    config_file = Path(".grkrc")
    if not config_file.exists():
        return {}
    try:
        yaml = YAML()
        with config_file.open("r") as f:
            full_config = yaml.load(f) or {}
        profiles = full_config.get("profiles", {})
        return profiles.get(profile, {})
    except Exception as e:
        print(f"Warning: Failed to load .grkrc profile '{profile}': {str(e)}")
        return {}
