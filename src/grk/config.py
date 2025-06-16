from pathlib import Path
from ruamel.yaml import YAML
import click  # For error handling and messages

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
                "model": "grok-3-mini-fast",
                "role": "python-programmer",
                "output": "output.txt",
                "json_out": "/tmp/grk_default_output.json",
                "prompt_prepend": "",
                "temperature": 0
            },
            "py": {
                "model": "grok-3-mini-fast",
                "role": "python-programmer",
                "output": "output.txt",
                "json_out": "/tmp/grk_py_output.json",
                "prompt_prepend": "",
                "temperature": 0
            },
            "doc": {
                "model": "grok-3",
                "role": "documentation-specialist",
                "output": "output.txt",
                "json_out": "/tmp/grk_doc_output.json",
                "prompt_prepend": "",
                "temperature": 0.7
            },
            "law": {
                "model": "grok-3-fast",
                "role": "senior lawyer/legal scholar",
                "output": "output.txt",
                "json_out": "/tmp/grk_law_output.json",
                "prompt_prepend": "write concise legal argumentation, prefer latex, use the cenum environment for continuous numbering throughout the document. ",
                "temperature": 0.5
            },
            "psy": {
                "model": "grok-3",
                "role": "senior psychologist",
                "output": "output.txt",
                "json_out": "/tmp/grk_psy_output.json",
                "prompt_prepend": """use standard psychological argumentation, write concise, use established psychological concepts from ICD10 and DSM5, use latex, assume cenum environment is available for continous numbering.""",
                "temperature": 0.5
            },
        }
    }

    for profile_name, profile_data in old_profiles.items():
        if profile_name in default_config["profiles"]:
            if profile_data != default_config["profiles"][profile_name]:
                default_config["profiles"][f"{profile_name}_old"] = profile_data
                click.echo(f"Profile '{profile_name}' differs from default, saved old as '{profile_name}_old'.")
        else:
            default_config["profiles"][f"{profile_name}_old"] = profile_data
            click.echo(f"Profile '{profile_name}' not in default config, saved as '{profile_name}_old'.")

    try:
        yaml = YAML()
        with open(".grkrc", "w") as f:
            yaml.dump(default_config, f)
        click.echo("Default .grkrc with profiles created successfully.")
    except Exception as e:
        click.echo(f"Failed to create .grkrc: {str(e)}")
