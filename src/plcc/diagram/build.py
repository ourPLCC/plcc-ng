import enum
import shutil
import subprocess
import sys

from docopt import docopt

from ..verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-diagram-build
    Dispatch to the appropriate plcc-diagram-<fmt>-build command.

Usage:
    plcc-diagram-build --input=FILE --output=FILE [-v ...] [options]

Options:
    --format=FMT    Diagram format [default: plantuml].
    --input=FILE    Path to diagram source file.
    --output=FILE   Path to write image file.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-diagram-build", Events, args)
    fmt = args['--format']
    input_file = args['--input']
    output_file = args['--output']
    cmd = f'plcc-diagram-{fmt}-build'
    if not shutil.which(cmd):
        print(
            f"No diagram build plugin found for '{fmt}'. Is {cmd} installed?\n"
            f"Run plcc-diagram-list to see what is available.",
            file=sys.stderr,
        )
        sys.exit(1)
    result = subprocess.run(
        [cmd, f'--input={input_file}', f'--output={output_file}'] + verbose.child_flags(),
    )
    if result.returncode != 0:
        sys.exit(result.returncode)
