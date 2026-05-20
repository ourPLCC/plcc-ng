"""plcc-python-run
    Run a generated Python interpreter.

Usage:
    plcc-python-run --output=DIR [-v ...] [options]

Options:
    --output=DIR    Directory containing generated Python files.
    -h --help       Show this message.
"""

import enum
import os
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
    verbose = VerboseContext.from_args("plcc-python-run", Events, args)
    output_dir = args['--output']
    main_py = os.path.join(output_dir, 'main.py')
    verbose.emit(Events.STARTED, message=f'running {main_py}')
    try:
        result = subprocess.run(
            [sys.executable, '-u', main_py],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
    except KeyboardInterrupt:
        sys.exit(130)
    verbose.emit(Events.FINISHED, message=f'exit {result.returncode}')
    sys.exit(result.returncode)
