import enum
import json
import sys

from docopt import docopt

from .build_model import build_model
from ..verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-model
    Transform spec JSON into a language-neutral code model.

Usage:
    plcc-model [-v ...] [options] [SPEC_JSON]

Arguments:
    SPEC_JSON   Path to spec JSON file. Use - or omit to read from stdin.

Options:
    -h --help   Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-model", Events, args)
    path = args['SPEC_JSON'] or '-'
    spec = _load(path)
    model = build_model(spec)
    print(json.dumps(model, indent=2))


def _load(path):
    if path == '-':
        return json.load(sys.stdin)
    with open(path) as f:
        return json.load(f)
