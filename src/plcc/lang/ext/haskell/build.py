"""plcc-haskell-build
    Build a generated Haskell interpreter with cabal.

Usage:
    plcc-haskell-build --output=DIR [-v ...] [options]

Options:
    --output=DIR    Directory containing generated Haskell files.
    -h --help       Show this message.
"""

import enum
import subprocess
import sys

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = __doc__ + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-haskell-build", Events, args)
    output_dir = args['--output']
    verbose.emit(Events.STARTED, message=f'building in {output_dir}')
    result = subprocess.run(
        ['cabal', 'build'],
        cwd=output_dir,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    verbose.emit(Events.FINISHED, message=f'exit {result.returncode}')
    sys.exit(result.returncode)
