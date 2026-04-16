"""plcc-parser-list
    List installed parser plugins.

Usage:
    plcc-parser-list

Options:
    -h --help   Show this message.
"""

import os
import re
import sys

from docopt import docopt

_PARSER_PATTERN = re.compile(r"^plcc-parser-(.+)$")


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    docopt(__doc__, argv)
    for kind in sorted(find_parsers()):
        print(kind)


def find_parsers():
    parsers = []
    seen = set()
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        try:
            for entry in os.scandir(directory):
                name = _extract_parser_kind(entry.name)
                if name and name not in seen and entry.is_file() and os.access(entry.path, os.X_OK):
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
