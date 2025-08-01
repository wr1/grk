"""Load and manage configuration using Pydantic for validation."""

from pathlib import Path
from ruamel.yaml import YAML
from .models import FullConfig, ProfileConfig  # Import Pydantic models
import click


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
            return profile_data  # Return the existing ProfileConfig object
        return ProfileConfig()  # Return empty if profile not found
    except Exception as e:
        print(f"Warning: Failed to load .grkrc profile '{profile}': {str(e)}")
        return ProfileConfig()


def create_default_config():
    """Create default .grkrc file with profiles, preserving old profiles with _old suffix if different."""
    config_file = Path(".grkrc")
    old_profiles = {}
    if config_file.exists():
        try:
            yaml = YAML()
            with config_file.open("r") as f:
                existing_config = yaml.load(f) or {}
            old_profiles = existing_config.get("profiles", {})
        except Exception as e:
            click.echo(f"Warning: Failed to load existing .grkrc: {str(e)}")

    default_config = {
        "profiles": {
            "default": {
                "model": "grok-4",
                "role": "you are an expert engineer and dev",
                "output": "output.txt",
                "json_out": "grk_default_output.json",
                "prompt_prepend": "",
                "temperature": 0.25,
            },
            "py": {
                "model": "grok-3-mini-fast",
                "role": "you are an expert python programmer, writing clean code",
                "output": "output.txt",
                "json_out": "grk_py_output.json",
                "prompt_prepend": "",
                "temperature": 0,
            },
            "doc": {
                "model": "grok-3",
                "role": "you are an expert in writing documentation",
                "output": "output.txt",
                "json_out": "grk_doc_output.json",
                "prompt_prepend": "",
                "temperature": 0.7,
            },
            "law": {
                "model": "grok-4",
                "role": "you are an expert lawyer, providing legal advice",
                "output": "output.txt",
                "json_out": "grk_law_output.json",
                "prompt_prepend": "write concise legal argumentation, prefer latex",
                "temperature": 0.35,
            },
            "psy": {
                "model": "grok-4",
                "role": "you are an expert professor in psychology",
                "output": "output.txt",
                "json_out": "grk_psy_output.json",
                "prompt_prepend": "",
                "temperature": 0.3,
            },
        }
    }

    # Add old profiles with _old suffix only if they differ
    for profile_name, profile_data in old_profiles.items():
        if profile_name in default_config["profiles"]:
            if profile_data != default_config["profiles"][profile_name]:
                default_config["profiles"][f"{profile_name}_old"] = profile_data
                click.echo(
                    f"Profile '{profile_name}' differs from default, saved old as '{profile_name}_old'."
                )
        else:
            default_config["profiles"][f"{profile_name}_old"] = profile_data
            click.echo(
                f"Profile '{profile_name}' not in default config, saved as '{profile_name}_old'."
            )

    try:
        yaml = YAML()
        with open(".grkrc", "w") as f:
            yaml.dump(default_config, f)
        click.echo("Default .grkrc with profiles created successfully.")
    except Exception as e:
        click.echo(f"Failed to create .grkrc: {str(e)}")
