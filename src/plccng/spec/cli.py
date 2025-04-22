'''plccng spec
    Verify a PLCC spec file, and print it as a JSON string.

Usage:
    plccng spec [FILE]

Options:
    FILE
        The spec file. If none is given, read from stdin.
'''

from dataclasses import asdict
import json
import sys

from docopt import docopt

from . import parseSpec


def run(argv):
    Cli().run(argv[1:])

class Cli:
    def run(self, argv):
        doc = sys.modules[Cli.__module__].__doc__
        args = docopt(doc, argv)
        if 'FILE' not in args or not args['FILE']:
            source = sys.stdin
            spec, errors = parseSpec(source.read(), '-')
        else:
            with open(args['FILE'], 'r') as source:
                spec, errors = parseSpec(source.read(), args['FILE'])
        if errors:
            for e in errors:
                print(e)
        else:
            print(json.dumps(asdict(spec), indent=2))
