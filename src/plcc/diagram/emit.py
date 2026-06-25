import enum
import shutil
import subprocess
import sys

from plcc.cli import parse_args

from ..verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-diagram-emit
    Dispatch model JSON to the appropriate plcc-diagram-{type}-{fmt}-emit command.

Usage:
    plcc-diagram-emit --type=TYPE [-v ...] [options]

Options:
    --type=TYPE     Diagram type (e.g., class).
    --format=FMT    Diagram format [default: plantuml].
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-diagram-emit", Events, args)
    diagram_type = args['--type']
    fmt = args['--format']
    cmd = f'plcc-diagram-{diagram_type}-{fmt}-emit'
    if not shutil.which(cmd):
        print(
            f"No diagram plugin found for type='{diagram_type}' format='{fmt}'."
            f" Is {cmd} installed?\n"
            f"Run plcc-diagram-list to see what is available.",
            file=sys.stderr,
        )
        sys.exit(1)
    result = subprocess.run(
        [cmd] + verbose.child_flags(),
        stdin=sys.stdin,
    )
    if result.returncode != 0:
        sys.exit(result.returncode)
