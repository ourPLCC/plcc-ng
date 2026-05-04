import enum
import sys

from docopt import docopt

from ..lines import Line
from ..scan.matcher import Matcher
from ..scan.scanner import Scanner
from ..scan.Skip import Skip
from ..scan.LexError import LexError
from .spec_loader import load_lexical_rules
from .jsonl_formatter import format_record
from ..verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-tokens
    Tokenize stdin given a spec JSON file, output token JSONL.

Usage:
    plcc-tokens [options] SPEC_JSON

Arguments:
    SPEC_JSON   Path to spec JSON file (output of plcc-spec).

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
    verbose = VerboseContext.from_args("plcc-tokens", Events, args)
    rules = load_lexical_rules(args['SPEC_JSON'])
    matcher = Matcher(rules)
    scanner = Scanner(matcher)
    lines = _read_stdin_as_lines()
    for obj in scanner.scan(lines):
        if isinstance(obj, Skip):
            continue
        if isinstance(obj, LexError):
            verbose.emit_error(
                pos={
                    "file": obj.line.file,
                    "line": obj.line.number,
                    "column": obj.column,
                },
                message="unrecognized character",
            )
            sys.exit(1)
        print(format_record(obj), flush=True)


def _read_stdin_as_lines():
    for i, raw in enumerate(sys.stdin, start=1):
        yield Line(string=raw.rstrip('\n'), number=i, file='<stdin>')
