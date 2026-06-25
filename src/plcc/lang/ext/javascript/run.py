"""plcc-javascript-run
    Run a generated JavaScript interpreter.

Usage:
    plcc-javascript-run --output=DIR [-v ...] [options]

Options:
    --output=DIR    Directory containing generated JavaScript files.
    -h --help       Show this message.
"""

import enum
import os
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
    verbose = VerboseContext.from_args("plcc-javascript-run", Events, args)
    output_dir = args['--output']
    main_js = os.path.join(output_dir, 'main.js')
    verbose.emit(Events.STARTED, message=f'running {main_js}')
    try:
        result = subprocess.run(
            ['node', main_js],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
    except KeyboardInterrupt:
        sys.exit(130)
    verbose.emit(Events.FINISHED, message=f'exit {result.returncode}')
    sys.exit(result.returncode)
