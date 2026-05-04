import enum
import shutil
import subprocess
import sys

from docopt import docopt

from ..verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-diagram
    Dispatch to the appropriate plcc-<fmt>-diagram command.

Usage:
    plcc-diagram --output=DIR [options]

Options:
    --output=DIR    Directory to write diagram file(s) into.
    --format=FMT    Diagram format [default: plantuml].
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-diagram", Events, args)
    fmt = args['--format'] or 'plantuml'
    output = args['--output']
    cmd = f'plcc-{fmt}-diagram'
    if not shutil.which(cmd):
        print(
            f"No diagram plugin found for '{fmt}'. Is {cmd} installed?\n"
            f"Run plcc-diagram-list to see what is available.",
            file=sys.stderr,
        )
        sys.exit(1)
    result = subprocess.run(
        [cmd, f'--output={output}'] + verbose.child_flags(),
        stdin=sys.stdin,
    )
    if result.returncode != 0:
        sys.exit(result.returncode)
