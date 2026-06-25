import enum
import os
import re
import subprocess
import sys

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from plcc.cmd.spec import SPEC_OPTION, spec_flag_for_child

__doc__ = """plcc-diagram
    Generate all installed diagram types from a PLCC spec file.

Usage:
    plcc-diagram [-v ...] [options]

Options:
""" + SPEC_OPTION + """\
    -b --banner             Show the version and spec banner on stderr.
    -h --help               Show this message.
""" + VERBOSE_OPTIONS

_TYPE_PATTERN = re.compile(r'^plcc-diagram-([a-z][a-z0-9]*)$')
_RESERVED = frozenset({'emit', 'build', 'run', 'list'})


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    try:
        args = docopt(__doc__, argv)
    except DocoptExit as e:
        print(str(e), file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-diagram --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose = VerboseContext.from_args("plcc-diagram", Events, args)
    verbose.emit(Events.STARTED, message="generating diagrams")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    for diagram_type in sorted(find_types()):
        cmd = f'plcc-diagram-{diagram_type}'
        result = subprocess.run(
            [cmd]
            + spec_flag_for_child(args)
            + (['--banner'] if args['--banner'] else [])
            + child_flags,
            stderr=subprocess.PIPE,
        )
        if result.stderr:
            events = verbose.parse_child_events(result.stderr.decode('utf-8', errors='replace'))
            verbose.reformat_child_events(events)
        if result.returncode != 0:
            sys.exit(result.returncode)

    verbose.emit(Events.FINISHED, message="done")


def find_types():
    types = []
    seen = set()
    for directory in _path_dirs():
        try:
            for entry in os.scandir(directory):
                name = _extract_type_name(entry.name)
                if name and name not in seen and _is_executable(entry):
                    types.append(name)
                    seen.add(name)
        except (PermissionError, FileNotFoundError):
            continue
    return types


def _extract_type_name(command_name):
    m = _TYPE_PATTERN.match(command_name)
    if not m:
        return None
    name = m.group(1)
    if name in _RESERVED:
        return None
    return name


def _path_dirs():
    return os.environ.get('PATH', '').split(os.pathsep)


def _is_executable(entry):
    return entry.is_file() and os.access(entry.path, os.X_OK)
