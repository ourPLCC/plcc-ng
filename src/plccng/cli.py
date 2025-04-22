"""
Usage:
  plccng scan --spec=SPEC [FILE ...]
  plccng spec [FILE]
  plccng (-h | --help)

from plccng.scanner import cli as scanner_cli


def cli(argv):
    Cli().run(argv)


class Cli:
    def __init__(self):
        ...

    def run(self, argv):
        if argv and argv[0] == 'scan':
            scanner_cli(argv[1:])
        else:
            doc = sys.modules[Cli.__module__].__doc__
            print(doc)

import sys

from docopt import docopt

from . import scanner
from . import spec

def main():
    doc = sys.modules[main.__module__].__doc__
    args = docopt(doc)
    if args["scan"]:
        scanner.run(args)
    elif args['spec']:
        spec.cli.run(sys.argv)
    else:
        print("Invalid Command, Enter 'plccng -h' for help")
