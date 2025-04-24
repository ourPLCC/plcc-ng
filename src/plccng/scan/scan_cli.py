"""scan
    Print token in JSON given PLCC specification and input files.

Usage:
    scan SPEC [FILE ...]
    scan (-h|--help)

Arguments:
    SPEC    File containing PLCC spec.
    FILE    A sequence of input files. If none are given, stdin is used.
            If '-' is given for a file, stdin is used.
"""

import sys

from docopt import docopt

from ..spec import parseSpec
from .matcher import Matcher
from .scanner import Scanner
from .sink import Sink
from .source import Source


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
            self._scan(spec, args['FILE'])

    def _loadSpec(self, file):
        with open(file, 'r') as f:
            contents = f.read()
        spec, errors = parseSpec(contents, file=file)
        return spec,errors

    def _printErrors(self, errors):
        for e in errors:
            print(e)

    def _scan(self, spec, sourceFile):
        source = Source(sourceFile)
        sink = Sink(printSkips=False)
        matcher = Matcher(spec.lexical.ruleList)
        scanner = Scanner(matcher)
        for thing in scanner.scan(source):
            sink.write(thing)
