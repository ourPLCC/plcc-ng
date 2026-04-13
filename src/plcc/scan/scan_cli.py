"""scan
    Print tokens in input string given PLCC specification.

Usage:
    scan [options] SPEC [FILE ...]
    scan (-h|--help)

Arguments:
    SPEC    PLCC spec file.
    FILE    Input files. '-' is stdin.

Options:
    --json      Format output in JSON.
    --skips     Show skips.
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
            self._scan(
                spec=spec,
                sourceFile=args['FILE'],
                format_fn=formatText if not args['--json'] else formatJson,
                showSkips=args['--skips']
            )

    def _loadSpec(self, file):
        with open(file, 'r') as f:
            contents = f.read()
        spec, errors = parseSpec(contents, file=file)
        return spec,errors

    def _printErrors(self, errors):
        for e in errors:
            print(e)

    def _scan(self, spec, sourceFile, format_fn, showSkips):
        source = Source(sourceFile)
        sink = Sink(printSkips=showSkips, format_fn=format_fn)
        matcher = Matcher(spec.lexical.ruleList)
        scanner = Scanner(matcher)
        for thing in scanner.scan(source):
            sink.write(thing)
