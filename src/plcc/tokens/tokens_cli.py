import enum
import json
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
    plcc-tokens [-v ...] [options] SPEC_JSON [SOURCE ...]

Arguments:
    SPEC_JSON   Path to spec JSON file (output of plcc-spec).
    SOURCE      Source files to tokenize. Use '-' for stdin. Defaults to stdin.

Options:
    -h --help               Show this message.
    -t --trace              Include regex, source_line, attempts; emit skip records.
    --source-name=<label>   Override the source label for stdin [default: -].
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"
    SCANNING_FILE = "scanning"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-tokens", Events, args)
    trace = args['--trace']
    source_name = args['--source-name']
    rules = load_lexical_rules(args['SPEC_JSON'])
    matcher = Matcher(rules, record_attempts=trace)
    scanner = Scanner(matcher)
    sources = args['SOURCE'] or ['-']
    verbose.emit(Events.STARTED, message="tokenizing")
    lines = _lines_from_sources(sources, verbose, source_name)
    first_label = (source_name or "-") if sources[0] == "-" else sources[0]
    last_source = {"file": first_label, "line": 1, "column": 1}
    for obj in scanner.scan(lines):
        if isinstance(obj, Skip):
            if trace:
                last_source = {"file": obj.line.file, "line": obj.line.number, "column": obj.column}
                print(format_record(obj, show_all=True), flush=True)
            continue
        if isinstance(obj, LexError):
            print(format_error_record(obj), flush=True)
            continue
        last_source = {"file": obj.line.file, "line": obj.line.number, "column": obj.column}
        print(format_record(obj, show_all=trace), flush=True)
    print(json.dumps({"kind": "token", "name": "eof", "lexeme": "", "source": last_source}), flush=True)
    verbose.emit(Events.FINISHED, message="done")


def _lines_from_sources(sources, verbose, source_name=None):
    for file in sources:
        verbose.emit(Events.SCANNING_FILE, level=1, message=f"scanning {file}")
        if file == '-':
            label = source_name if source_name else '-'
            yield from _lines_from_stream(sys.stdin, label)
        else:
            with open(file, 'r') as f:
                yield from _lines_from_stream(f, file)


def _lines_from_stream(stream, file):
    for i, raw in enumerate(stream, start=1):
        yield Line(string=raw.rstrip('\n'), number=i, file=file)
