"""Load and manage configuration using Pydantic for validation."""

from pathlib import Path
from ruamel.yaml import YAML
from .models import FullConfig, ProfileConfig, Brief  # Import Pydantic models
from typing import Optional
from .logging import setup_logging

logger = setup_logging()

DEFAULT_PROFILES = {
    "default": {
        "model": "grok-4",
        "role": "you are an expert engineer and developer",
        "output": "output.json",
        "prompt_prepend": "",
        "temperature": 0.25,
    },
    "py": {
        "model": "grok-4",
        "role": "you are an expert python programmer, writing clean code",
        "output": "output.json",
        "prompt_prepend": "",
        "temperature": 0,
    },
    "doc": {
        "model": "grok-4",
        "role": "you are an expert in writing documentation",
        "output": "output.json",
        "prompt_prepend": "",
        "temperature": 0.7,
    },
    "law": {
        "model": "grok-4",
        "role": "you are an expert lawyer, providing legal advice",
        "output": "output.json",
        "prompt_prepend": "write concise legal argumentation, prefer latex",
        "temperature": 0.35,
    },
    "psy": {
        "model": "grok-4",
        "role": "you are an expert professor in psychology",
        "output": "output.json",
        "prompt_prepend": "",
        "temperature": 0.3,
    },
}

DEFAULT_BRIEF = {"file": "design_brief.typ", "role": "assistant"}


def load_config(profile: str = "default") -> ProfileConfig:
    """Load specified profile from .grkrc YAML config file and validate with Pydantic, falling back to defaults if not present."""
    config_file = Path(".grkrc")
    if not config_file.exists():
        profile_data = DEFAULT_PROFILES.get(profile, {})
        return ProfileConfig(**profile_data)
    try:
        yaml = YAML()
        with config_file.open("r") as f:
            data = yaml.load(f) or {}
        full_config = FullConfig(**data)  # Parse into FullConfig for validation
        profile_data = full_config.profiles.get(profile)
        if profile_data:
            return profile_data  # Return the existing ProfileConfig object
        # Fallback to default if profile not found
        default_data = DEFAULT_PROFILES.get(profile, {})
        return ProfileConfig(**default_data)
    except Exception as e:
        logger.warning(f"Failed to load .grkrc profile '{profile}': {str(e)}")
        # Fallback on error
        default_data = DEFAULT_PROFILES.get(profile, {})
        return ProfileConfig(**default_data)


def load_brief() -> Optional[Brief]:
    """Load the top-level brief from .grkrc, falling back to default if file not present."""
    config_file = Path(".grkrc")
    if not config_file.exists():
        return Brief(**DEFAULT_BRIEF)
    try:
        yaml = YAML()
        with config_file.open("r") as f:
            data = yaml.load(f) or {}
        full_config = FullConfig(**data)
        return full_config.brief
    except Exception as e:
        logger.warning(f"Failed to load brief from .grkrc: {str(e)}")
        return None


def create_default_config():
    """Create default .grkrc file with profiles, preserving old profiles with _old suffix if different."""
    config_file = Path(".grkrc")
    old_profiles = {}
    old_brief = None
    if config_file.exists():
        try:
            yaml = YAML()
            with config_file.open("r") as f:
                existing_config = yaml.load(f) or {}
            old_profiles = existing_config.get("profiles", {})
            old_brief = existing_config.get("brief")
        except Exception as e:
            logger.warning(f"Failed to load existing .grkrc: {str(e)}")

    default_config = {
        "profiles": DEFAULT_PROFILES,
        "brief": DEFAULT_BRIEF,
    }

    # Add old profiles with _old suffix only if they differ
    for profile_name, profile_data in old_profiles.items():
        if profile_name in default_config["profiles"]:
            if profile_data != default_config["profiles"][profile_name]:
                default_config["profiles"][f"{profile_name}_old"] = profile_data
                logger.info(
                    f"Profile '{profile_name}' differs from default, saved old as '{profile_name}_old'."
                )
        else:
            default_config["profiles"][f"{profile_name}_old"] = profile_data
            logger.info(
                f"Profile '{profile_name}' not in default config, saved as '{profile_name}_old'."
            )

    # Preserve old brief if different
    if old_brief and old_brief != default_config.get("brief"):
        default_config["brief_old"] = old_brief
        logger.info("Brief differs from default, saved old as 'brief_old'.")

    try:
        yaml = YAML()
        with open(".grkrc", "w") as f:
            yaml.dump(default_config, f)
        logger.info("Default .grkrc with profiles created successfully.")
    except Exception as e:
        logger.error(f"Failed to create .grkrc: {str(e)}")
