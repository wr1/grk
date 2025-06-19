"""Load and manage configuration using Pydantic for validation."""
from pathlib import Path
from ruamel.yaml import YAML
from .models import FullConfig, ProfileConfig  # Import Pydantic models

def load_config(profile: str = "default") -> ProfileConfig:
    """Load specified profile from .grkrc YAML config file and validate with Pydantic."""
    config_file = Path(".grkrc")
    if not config_file.exists():
        return ProfileConfig()  # Return empty ProfileConfig
    try:
        yaml = YAML()
        with config_file.open("r") as f:
            data = yaml.load(f) or {}
        full_config = FullConfig(**data)  # Parse into FullConfig for validation
        profile_data = full_config.profiles.get(profile)
        if profile_data:
            return ProfileConfig(**profile_data)  # Return validated ProfileConfig
        return ProfileConfig()  # Return empty if profile not found
    except Exception as e:
        print(f"Warning: Failed to load .grkrc profile '{profile}': {str(e)}")
        return ProfileConfig()
