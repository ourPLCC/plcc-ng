import enum
import shutil
import subprocess
import sys

from docopt import docopt

from ..verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-diagram-emit
    Dispatch model JSON to the appropriate plcc-<fmt>-diagram-emit command.

Usage:
    plcc-diagram-emit [-v ...] [options]

Options:
    --format=FMT    Diagram format [default: mermaid].
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-diagram-emit", Events, args)
    fmt = args['--format']
    cmd = f'plcc-{fmt}-diagram-emit'
    if not shutil.which(cmd):
        print(
            f"No diagram plugin found for '{fmt}'. Is {cmd} installed?\n"
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
