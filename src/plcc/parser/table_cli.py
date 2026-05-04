import enum
import json
import sys

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from .predictive_parser import parse, ParseError

__doc__ = """plcc-parser-table
    Table-driven LL(1) parser. Reads token JSONL from stdin, emits a parse tree.

Usage:
    plcc-parser-table [options] --ll1=LL1_JSON

Options:
    --ll1=LL1_JSON          Path to LL(1) analysis JSON (required).
    -h --help               Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"
    EXPAND = "expand"
    SHIFT = "shift"
    COMPLETE = "complete"
    PREDICT_LOOKUP = "predict-lookup"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-parser-table", Events, args)
    ll1_path = args["--ll1"]
    verbose.emit(Events.STARTED, ll1_path=ll1_path)

    # Load ll1.json
    try:
        with open(ll1_path) as f:
            ll1 = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        verbose.emit_error({}, f"cannot load ll1.json from {ll1_path!r}: {e}")
        sys.exit(1)

    if not ll1.get("is_ll1", False):
        verbose.emit_error({}, "grammar is not LL(1); cannot parse")
        sys.exit(1)

    # Read all records from stdin; pass error records through unchanged.
    tokens = []
    error_record = None
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as e:
            verbose.emit_error({}, f"malformed token JSON: {e}")
            sys.exit(1)
        if record.get("kind") == "error":
            error_record = record
        else:
            tokens.append(record)

    if error_record is not None:
        print(json.dumps(error_record))
        sys.exit(0)

    # Parse
    try:
        tree = parse(ll1, tokens)
    except ParseError as e:
        verbose.emit_error({}, str(e))
        sys.exit(1)

    verbose.emit(Events.FINISHED, token_count=len(tokens), rule_count=_count_rules(tree))
    print(json.dumps(tree))


def _count_rules(node):
    """Count internal (tree-kind) nodes in the parse tree."""
    if isinstance(node, list):
        return sum(_count_rules(item) for item in node)
    if node.get("kind") != "tree":
        return 0
    return 1 + sum(_count_rules(child[1]) for child in node.get("children", []))
