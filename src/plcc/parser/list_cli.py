import enum
import os
import re
import sys

from plcc.cli import parse_args

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

_PARSER_PATTERN = re.compile(r"^plcc-parser-(.+)$")

__doc__ = """plcc-parser-list
    List installed parser plugins.

Usage:
    plcc-parser-list [-v ...] [options]

Options:
    -h --help   Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(__doc__, argv)
    VerboseContext.from_args("plcc-parser-list", Events, args)
    for kind in sorted(find_parsers()):
        print(kind)


def find_parsers():
    """Scan PATH for plcc-parser-* commands; return list of parser kinds."""
    parsers = []
    seen = set()
    for directory in _path_dirs():
        try:
            for entry in os.scandir(directory):
                name = _extract_parser_kind(entry.name)
                if name and name not in seen and _is_executable(entry):
                    parsers.append(name)
                    seen.add(name)
        except (PermissionError, FileNotFoundError):
            continue
    return parsers


def _extract_parser_kind(command_name):
    m = _PARSER_PATTERN.match(command_name)
    if m:
        kind = m.group(1)
        if kind != "list":
            return kind
    return None


def _path_dirs():
    return os.environ.get("PATH", "").split(os.pathsep)


def _is_executable(entry):
    return entry.is_file() and os.access(entry.path, os.X_OK)
