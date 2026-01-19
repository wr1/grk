"""Single-shot CLI commands."""

import os
from pathlib import Path
from ..config.config import load_config
from ..core.runner import run_grok
from ..utils.utils import GrkException
from treeparse import group, command, argument, option
from typing import Optional


def run_func(file: str, message: str, profile: str = "default", output: str = None):
    """Run the Grok LLM processing using the specified profile (single-shot mode)."""
    if not Path(file).exists() or Path(file).is_dir():
        raise GrkException(f"Invalid file: {file}")
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise GrkException("API key is required via XAI_API_KEY environment variable.")
    config = load_config(profile)
    run_grok(file, message, config, api_key, profile, output=output)


single_grp = group(
    name="single",
    help="Single-Shot mode, run one-off queries to Grok.",
)

run_cmd = command(
    name="run",
    help="Run the Grok LLM processing using the specified profile (single-shot mode).",
    callback=run_func,
    arguments=[
        argument(name="file", arg_type=str, sort_key=0),
        argument(name="message", arg_type=str, sort_key=1),
    ],
    options=[
        option(
            flags=["--profile", "-p"],
            help="The profile to use",
            arg_type=str,
            default="default",
            sort_key=0,
        ),
        option(
            flags=["--output", "-o"],
            help="Output file for the response",
            arg_type=str,
            default=None,
            sort_key=1,
        ),
    ],
)
single_grp.commands.append(run_cmd)
