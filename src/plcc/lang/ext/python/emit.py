"""plcc-python-emit
    Emit a stub Python interpreter from model JSON.

Usage:
    plcc-python-emit --output=DIR [options]

Options:
    --output=DIR    Directory to write output files into.
    -h --help       Show this message.
"""

import enum
import os
import shutil
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
    verbose = VerboseContext.from_args("plcc-python-emit", Events, args)
    output_dir = args['--output']
    verbose.emit(Events.STARTED, message=f'emitting to {output_dir}')
    # Read and discard model JSON from stdin (required by contract)
    sys.stdin.read()
    os.makedirs(output_dir, exist_ok=True)
    runtime_dir = os.path.join(os.path.dirname(__file__), "runtime")
    shutil.copy2(os.path.join(runtime_dir, "main.py"), os.path.join(output_dir, "main.py"))
    verbose.emit(Events.FINISHED, message="done")
