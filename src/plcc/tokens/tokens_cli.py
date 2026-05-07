import enum
import sys

from docopt import docopt

from ..lines import Line
from ..scan.matcher import Matcher
from ..scan.scanner import Scanner
from ..scan.Skip import Skip
from ..scan.LexError import LexError
from .spec_loader import load_lexical_rules
from .jsonl_formatter import format_record, format_error_record
from ..verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-tokens
    Tokenize source files given a spec JSON file, output token JSONL.

Usage:
    plcc-tokens [options] SPEC_JSON [SOURCE ...]

Arguments:
    SPEC_JSON   Path to spec JSON file (output of plcc-spec).
    SOURCE      Source files to tokenize. Use '-' for stdin. Defaults to stdin.

Options:
    -h --help               Show this message.
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
    sources = args['SOURCE'] or ['-']
    lines = _lines_from_sources(sources)
    for obj in scanner.scan(lines):
        if isinstance(obj, Skip):
            continue
        if isinstance(obj, LexError):
            print(format_error_record(obj), flush=True)
            continue
        print(format_record(obj), flush=True)


def _lines_from_sources(sources):
    for file in sources:
        if file == '-':
            yield from _lines_from_stream(sys.stdin, '-')
        else:
            with open(file, 'r') as f:
                yield from _lines_from_stream(f, file)


def _lines_from_stream(stream, file):
    for i, raw in enumerate(stream, start=1):
        yield Line(string=raw.rstrip('\n'), number=i, file=file)
