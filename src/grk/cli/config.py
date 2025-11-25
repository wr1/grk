"""Config CLI commands."""

import os
from ..config.config import create_default_config
from ..config.config_handler import list_configs
from treeparse import group, command


def init_func():
    """Initialize .grkrc with default profiles."""
    create_default_config()


def list_func():
    """List the configurations from .grkrc with YAML syntax highlighting."""
    list_configs()

config_grp = group(
    name="config",
    help="Manage configuration.",
)

init_cmd = command(
    name="init",
    help="Initialize .grkrc with default profiles.",
    callback=init_func,
)
config_grp.commands.append(init_cmd)

list_cmd = command(
    name="list",
    help="List the configurations from .grkrc with YAML syntax highlighting.",
    callback=list_func,
)
config_grp.commands.append(list_cmd)
