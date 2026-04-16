import enum
import json
import sys

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-parser-table
    Table-driven LL(1) parser. Reads token JSONL, emits a parse tree.

Usage:
    plcc-parser-table [options] --ll1=LL1_JSON

Options:
    --ll1=LL1_JSON          Path to LL(1) analysis JSON (required).
    -h --help               Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-parser-table", Events, args)
    ll1_path = args["--ll1"]
    verbose.emit(Events.STARTED, message=f"parsing with table from {ll1_path}")
    # Stub: wrap each token in a minimal tree, pass errors through unchanged.
    # This is the Phase 1 plcc-tree behavior, relocated here.
    children = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        if record.get("kind") == "error":
            children.append(record)
        else:
            children.append(record)
    tree = {
        "kind": "tree",
        "rule": "program",
        "children": children,
    }
    print(json.dumps(tree), flush=True)
    verbose.emit(Events.FINISHED, message="done")
