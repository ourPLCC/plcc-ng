"""plcc-haskell-run
    Run a generated Haskell interpreter.

Usage:
    plcc-haskell-run --output=DIR [-v ...] [options]

Options:
    --output=DIR    Directory containing generated Haskell files.
    -h --help       Show this message.
"""

import enum
import subprocess
import sys

from plcc.cli import parse_args

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = __doc__ + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-haskell-run", Events, args)
    output_dir = args['--output']
    verbose.emit(Events.STARTED, message=f'running in {output_dir}')
    try:
        result = subprocess.run(
            ['cabal', 'run', 'interpreter'],
            cwd=output_dir,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
    except KeyboardInterrupt:
        sys.exit(130)
    verbose.emit(Events.FINISHED, message=f'exit {result.returncode}')
    sys.exit(result.returncode)
