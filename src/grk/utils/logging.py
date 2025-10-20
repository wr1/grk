"""Logging configuration for grk."""

import logging
from rich.logging import RichHandler


def setup_logging():
    """Set up logging with RichHandler for rich formatting."""
    logging.basicConfig(
        level="INFO",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, show_time=False)],
    )
    return logging.getLogger("grk")
