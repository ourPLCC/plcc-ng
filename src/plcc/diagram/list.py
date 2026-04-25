import enum
import os
import re
import sys

from docopt import docopt

from ..verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-diagram-list
    List installed diagram plugins.

Usage:
    plcc-diagram-list [options]

Options:
    -h --help   Show this message.
""" + VERBOSE_OPTIONS

_DIAGRAM_PATTERN = re.compile(r'^plcc-(.+)-diagram$')


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-diagram-list", Events, args)
    for fmt in sorted(find_formats()):
        print(fmt)


def find_formats():
    """Scan PATH for plcc-*-diagram commands; return list of format names."""
    formats = []
    seen = set()
    for directory in _path_dirs():
        try:
            for entry in os.scandir(directory):
                name = extract_format_name(entry.name)
                if name and name not in seen and _is_executable(entry):
                    formats.append(name)
                    seen.add(name)
        except (PermissionError, FileNotFoundError):
            continue
    return formats


def extract_format_name(command_name):
    """Return format name from plcc-<fmt>-diagram command name, or None."""
    m = _DIAGRAM_PATTERN.match(command_name)
    if m:
        fmt = m.group(1)
        if fmt != 'diagram':
            return fmt
    return None


def _path_dirs():
    return os.environ.get('PATH', '').split(os.pathsep)


def _is_executable(entry):
    return entry.is_file() and os.access(entry.path, os.X_OK)
