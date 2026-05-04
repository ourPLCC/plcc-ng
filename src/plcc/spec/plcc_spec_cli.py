import enum
import json
import sys
from dataclasses import asdict

from docopt import docopt

from . import parseSpec
from ..verbose import VerboseContext, VERBOSE_OPTIONS

# No LL(1) analysis here; see plcc-ll1.
__doc__ = """plcc-spec
    Parse, validate, and print a PLCC grammar file as JSON.

Usage:
    plcc-spec [options] FILE

Arguments:
    FILE    PLCC grammar file. Use - to read from stdin.

Options:
    --no-json       Do not print JSON to stdout.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-spec", Events, args)
    spec, errors = _load(args['FILE'])
    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        sys.exit(1)
    if not args['--no-json']:
        print(json.dumps(asdict(spec), indent=2))


def _load(path):
    if path == '-':
        return parseSpec(sys.stdin.read(), '-')
    with open(path) as f:
        return parseSpec(f.read(), path)
