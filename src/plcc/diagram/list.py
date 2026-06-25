import enum
import os
import re
import sys

from docopt import docopt

from ..verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-diagram-list
    List installed diagram plugins.

Usage:
    plcc-diagram-list [-v ...] [options]

Options:
    -h --help   Show this message.
""" + VERBOSE_OPTIONS

_PLUGIN_PATTERN = re.compile(r'^plcc-diagram-([a-z][a-z0-9]*)-([a-z][a-z0-9]*)-emit$')


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-diagram-list", Events, args)
    for diagram_type, fmt in sorted(find_plugins()):
        print(f'{diagram_type}/{fmt}')


def find_plugins():
    plugins = []
    seen = set()
    for directory in _path_dirs():
        try:
            for entry in os.scandir(directory):
                result = extract_type_format(entry.name)
                if result and result not in seen and _is_executable(entry):
                    plugins.append(result)
                    seen.add(result)
        except (PermissionError, FileNotFoundError):
            continue
    return plugins


def extract_type_format(command_name):
    m = _PLUGIN_PATTERN.match(command_name)
    if not m:
        return None
    return (m.group(1), m.group(2))


def _path_dirs():
    return os.environ.get('PATH', '').split(os.pathsep)


def _is_executable(entry):
    return entry.is_file() and os.access(entry.path, os.X_OK)
