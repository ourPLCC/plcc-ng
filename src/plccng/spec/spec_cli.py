'''plccng spec
    Parse, validate, and print PLCC spec as a JSON structure.

Usage:
    plccng spec [options] FILE

Arguments:
    FILE    PLCC spec file. Use - to read from stdin.

Options:
    --no-json       Do not display JSON structure to stdout.
    --no-status     Do not display status to stderr.
    -h|--help       Display this message
'''

import json
import sys
from dataclasses import asdict

from docopt import docopt

from . import parseSpec


def run(argv):
    SpecCli().run(argv)


class SpecCli:
    def __init__(self):
        self._isStatusEnabled = False

    def run(self, argv):
        args = self._parseCommandLine(argv)
        if not args['--no-status']:
            self._enableStatus()
        spec, errors = self._loadSpec(args['FILE'])
        if errors:
            self._reportErrorsAndExit(errors)
        elif not args['--no-json']:
            print(json.dumps(asdict(spec), indent=2))
        self._status('No errors.')

    def _parseCommandLine(self, argv):
        doc = sys.modules[SpecCli.__module__].__doc__
        args = docopt(doc, argv)
        return args

    def _enableStatus(self):
        self._isStatusEnabled = True

    def _reportErrorsAndExit(self, errors):
        errors = list(errors)
        for e in errors:
            print(e, file=sys.stderr)
        self._status(f'{len(errors)} error(s).')
        sys.exit(1)

    def _loadSpec(self, file):
        if file == '-':
            self._status('Reading spec from stdin. Press ^D when finished.')
            spec, errors = self._parseFromStdin()
        else:
            self._status(f'Reading spec from {file}')
            spec, errors = self._parseFromFile(file)
        return spec,errors

    def _parseFromFile(self, file):
        with open(file, 'r') as source:
            spec, errors = parseSpec(source.read(), file)
        return spec,errors

    def _parseFromStdin(self):
        source = sys.stdin
        spec, errors = parseSpec(source.read(), '-')
        return spec, errors

    def _status(self, m):
        if self._isStatusEnabled:
            print(m, file=sys.stderr)

