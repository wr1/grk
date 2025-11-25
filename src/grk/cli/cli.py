"""Main CLI entry point for grk."""

from treeparse import cli
from .config import config_grp
from .single import single_grp
from .session import session_grp

app = cli(
    name="grk",
    help="CLI tool to interact with Grok.",
    max_width=120,
    show_types=True,
    show_defaults=True,
    line_connect=True,
)

app.subgroups.append(config_grp)
app.subgroups.append(single_grp)
app.subgroups.append(session_grp)


def main():
    try:
        app.run()
    except Exception as e:
        from rich.console import Console

        console = Console()
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        import sys

        sys.exit(1)


if __name__ == "__main__":
    main()
