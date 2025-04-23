'''spec
    Verify a PLCC spec, and print it as JSON.

Usage:
    spec [--] FILE
    spec (-h|--help)

Arguments:
    FILE        File containing the spec. Use - to read from stdin.
                If -- is given before FILE, then - is the name of the file.

Options:
    -h|--help   Display this message
    --          Treat - for FILE as a filename, not stdin.
'''

from dataclasses import asdict
import json
import sys

from docopt import docopt

from . import parseSpec


def cli(argv):
    argv = argv[1:]     # remove command name
    Cli().run(argv)


class Cli:
    def run(self, argv):
        doc = sys.modules[Cli.__module__].__doc__
        args = docopt(doc, argv, options_first=True)
        if args['FILE'] == '-':
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
