"""scan
    Print tokens in input string given PLCC specification.

Usage:
    scan [--json] SPEC [FILE ...]
    scan (-h|--help)

Arguments:
    SPEC    File containing PLCC spec.
    FILE    A sequence of input files. If none are given, stdin is used.
            If '-' is given for a file, stdin is used.

Options:
    --json  Format tokens and errors in JSON format.
"""

import sys

from docopt import docopt

from ..spec import parseSpec
from .json_formatter import format as formatJson
from .matcher import Matcher
from .scanner import Scanner
from .sink import Sink
from .source import Source
from .text_formatter import format as formatText


def run(argv):
    argv = argv[1:]
    ScanCli().run(argv)


class ScanCli:
    def run(self, argv):
        doc = sys.modules[ScanCli.__module__].__doc__
        args = docopt(doc, argv)
        spec, errors = self._loadSpec(args['SPEC'])
        if errors:
            self._printErrors(errors)
        else:
            f = formatText if not args['--json'] else formatJson
            self._scan(spec, args['FILE'], f)

    def _loadSpec(self, file):
        with open(file, 'r') as f:
            contents = f.read()
        spec, errors = parseSpec(contents, file=file)
        return spec,errors

    def _printErrors(self, errors):
        for e in errors:
            print(e)

    def _scan(self, spec, sourceFile, format_fn):
        source = Source(sourceFile)
        sink = Sink(printSkips=False, format_fn=format_fn)
        matcher = Matcher(spec.lexical.ruleList)
        scanner = Scanner(matcher)
        for thing in scanner.scan(source):
            sink.write(thing)
