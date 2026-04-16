import enum
import json
import sys

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-ll1
    Perform LL(1) analysis on a grammar spec.

Usage:
    plcc-ll1 [options] [SPEC_JSON]

Arguments:
    SPEC_JSON   Path to spec JSON file. Use - or omit to read from stdin.

Options:
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-ll1", Events, args)
    verbose.emit(Events.STARTED, message="reading spec")
    path = args['SPEC_JSON'] or '-'
    if path == '-':
        json.load(sys.stdin)
    else:
        with open(path) as f:
            json.load(f)
    # Stub: emit minimal ll1.json with empty sets
    result = {
        "first_sets": {},
        "follow_sets": {},
        "predict_sets": {},
        "parse_table": {},
        "conflicts": [],
        "left_recursion": [],
    }
    print(json.dumps(result, indent=2))
    verbose.emit(Events.FINISHED, message="done")
