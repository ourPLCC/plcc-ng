import enum
import shutil
import subprocess
import sys

from plcc.cli import parse_args

from ..verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-diagram-run
    Dispatch to the appropriate plcc-diagram-<fmt>-run command.

Usage:
    plcc-diagram-run --input=FILE [-v ...] [options]

Options:
    --format=FMT    Diagram format [default: plantuml].
    --input=FILE    Path to diagram image file.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-diagram-run", Events, args)
    fmt = args['--format']
    input_file = args['--input']
    cmd = f'plcc-diagram-{fmt}-run'
    if not shutil.which(cmd):
        print(
            f"No diagram run plugin found for '{fmt}'. Is {cmd} installed?\n"
            f"Run plcc-diagram-list to see what is available.",
            file=sys.stderr,
        )
        sys.exit(1)
    result = subprocess.run(
        [cmd, f'--input={input_file}'] + verbose.child_flags(),
    )
    if result.returncode != 0:
        sys.exit(result.returncode)
