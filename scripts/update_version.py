"""Simple CLI tool to update version of the application."""

from __future__ import annotations

from argparse import ArgumentParser
from enum import Enum
from pathlib import Path

BASE = Path(__file__).parent.parent
INIT_PATH = BASE / "image_secrets/__init__.py"
PYPROJECT_PATH = BASE / "pyproject.toml"

INIT_START = "__version__ = "
PYPROJECT_START = "version = "


class LineStart(str, Enum):
    """Enumeration of all `LineStart` values to identify each version line."""

    init = INIT_START
    pyproject = PYPROJECT_START


def get_init_line(version: str) -> str:
    """Return full version line to write into ``__init__.py`` file.

    :param version: New version string

    """
    return f'{INIT_START}"{version}"\n'


def get_pyproject_line(version: str) -> str:
    """Return full version line to write into ``pyproject.toml`` file.

    :param version: New version string

    """
    return f'{PYPROJECT_START}"{version}"\n'


def update_line_in_file(
    file: Path,
    line_start: LineStart,
    new_line: str,
) -> None:
    """Update a specific line to a new value.

    :param file: Path to the file to update
    :param line_start: Identifier of the line to update
    :param new_line: New line to insert into the identified line

    """
    with file.open() as input:
        lines = input.readlines()

    with file.open(mode="w") as output:
        for line in lines:
            to_write = new_line if line.startswith(line_start.value) else line
            output.write(to_write)


def get_parser() -> ArgumentParser:
    """Return Parser for CLI arguments."""
    p = ArgumentParser()
    p.add_argument(
        "version",
        type=str,
        help="new application version to set in all configuration files",
    )
    return p


def update_init(version: str) -> None:
    """Update the version ``__init__.py`` file.

    param version: New application version

    """
    new_line = get_init_line(version=version)
    update_line_in_file(
        file=INIT_PATH,
        line_start=LineStart.init,
        new_line=new_line,
    )


def update_pyproject(version: str) -> None:
    """Update the version in ``pyproject.toml`` file.

    param version: New application version

    """
    new_line = get_pyproject_line(version=version)
    update_line_in_file(
        file=PYPROJECT_PATH,
        line_start=LineStart.pyproject,
        new_line=new_line,
    )


UPDATE_FUNCTIONS = (update_init, update_pyproject)


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()

    ver = args.version

    for function in UPDATE_FUNCTIONS:
        function(version=ver)
