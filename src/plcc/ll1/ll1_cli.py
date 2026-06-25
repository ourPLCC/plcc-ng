import enum
import json
import sys

from plcc.cli import parse_args

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from .spec_json_decoder import decode
from .ll1_result_builder import build_ll1_result

__doc__ = """plcc-ll1
    Perform LL(1) analysis on a grammar spec.

Usage:
    plcc-ll1 [-v ...] [options]

Options:
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"
    FIRST_SET = "first-set"
    FOLLOW_SET = "follow-set"
    PREDICT_SET = "predict-set"
    CONFLICT = "conflict"
    LEFT_RECURSION = "left-recursion"
    FIXPOINT_STEP = "fixpoint-step"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-ll1", Events, args)
    verbose.emit(Events.STARTED)
    try:
        spec = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as e:
        verbose.emit_error({}, f"malformed spec JSON: {e}")
        sys.exit(1)
    grammar, productions, arbno_rules = decode(spec)
    result = build_ll1_result(grammar, productions, arbno_rules)
    for nt, terminals in result["first_sets"].items():
        verbose.emit(Events.FIRST_SET, level=2, nonterminal=nt, first=terminals)
    for nt, terminals in result["follow_sets"].items():
        verbose.emit(Events.FOLLOW_SET, level=2, nonterminal=nt, follow=terminals)
    for nt, predicts in result["predict_sets"].items():
        verbose.emit(Events.PREDICT_SET, level=2, nonterminal=nt, predict=predicts)
    for conflict in result["conflicts"]:
        verbose.emit(Events.CONFLICT, level=2, **conflict)
    for lr in result["left_recursion"]:
        verbose.emit(Events.LEFT_RECURSION, level=2, **lr)
    n_c = len(result["conflicts"])
    n_lr = len(result["left_recursion"])
    summary = (
        "is_ll1: true"
        if result["is_ll1"]
        else f"{n_c} conflicts, {n_lr} left-recursion cycles"
    )
    verbose.emit(Events.FINISHED, message=summary)
    print(json.dumps(result, indent=2))
