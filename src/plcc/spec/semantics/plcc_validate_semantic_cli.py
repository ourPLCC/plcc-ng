import enum
import json
import sys

from plcc.cli import parse_args
from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

from .deserialize import deserialize_semantic_spec
from .validation import validate_semantic_spec

__doc__ = """plcc-validate-semantic
    Validate the semantic section of a spec JSON.

Usage:
    plcc-validate-semantic [-v ...] [options]

Options:
    -h --help   Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-validate-semantic", Events, args)
    verbose.emit(Events.STARTED)
    try:
        spec = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as e:
        verbose.emit_error({}, f"malformed spec JSON: {e}")
        sys.exit(1)
    sem = deserialize_semantic_spec(spec)
    if sem is None:
        verbose.emit(Events.FINISHED, message="no semantics section")
        return
    errors = validate_semantic_spec(sem)
    if errors:
        for e in errors:
            pos = {"file": e.line.file, "line": e.line.number, "column": e.column}
            kwargs = {"source_line": e.line.string}
            if e.hint:
                kwargs["hint"] = e.hint
            verbose.emit_error(pos, e.kind, **kwargs)
        sys.exit(1)
    verbose.emit(Events.FINISHED, message="ok")
