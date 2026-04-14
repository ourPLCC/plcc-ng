"""plcc-tokens
    Tokenize stdin given a spec JSON file, output token JSONL.

Usage:
    plcc-tokens [options] SPEC_JSON

Arguments:
    SPEC_JSON   Path to spec JSON file (output of plcc-spec).

Options:
    -h --help   Show this message.
"""

import sys

from docopt import docopt

from ..lines import Line
from ..scan.matcher import Matcher
from ..scan.scanner import Scanner
from ..scan.Skip import Skip
from .spec_loader import load_lexical_rules
from .jsonl_formatter import format_record


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    rules = load_lexical_rules(args['SPEC_JSON'])
    matcher = Matcher(rules)
    scanner = Scanner(matcher)
    lines = _read_stdin_as_lines()
    for obj in scanner.scan(lines):
        if isinstance(obj, Skip):
            continue
        print(format_record(obj), flush=True)


def _read_stdin_as_lines():
    for i, raw in enumerate(sys.stdin, start=1):
        yield Line(string=raw.rstrip('\n'), number=i, file='<stdin>')
