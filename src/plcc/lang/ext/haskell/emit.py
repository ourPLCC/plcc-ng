"""plcc-haskell-emit
    Emit a Haskell interpreter from model JSON.

Usage:
    plcc-haskell-emit --output=DIR [-v ...] [options]

Options:
    --output=DIR    Directory to write output files into.
    -h --help       Show this message.
"""

import enum
import json
import shutil
import sys
from pathlib import Path

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
    verbose = VerboseContext.from_args("plcc-haskell-emit", Events, args)
    output_dir = Path(args['--output'])
    verbose.emit(Events.STARTED, message=f'emitting to {output_dir}')
    model = json.load(sys.stdin)
    emit(model, output_dir)
    verbose.emit(Events.FINISHED, message='done')


def emit(model, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
