"""plccng: Programming Languages Compiler Compiler - Next Generation

Usage:
    plccng COMMAND [OPTION ...] [ARGUMENT ...]
    plccng (-h|--help)

Commands:
    scan
        Print JSON tokens given PLCC spec and code.
    spec
        Print JSON representation of PLCC spec.
"""

import sys
from docopt import docopt

from . import scanner

def main():
    cli(sys.argv)


def cli(argv):
    Cli().run(argv)


class Cli:
    def __init__(self):
        ...

    def run(self, argv):
        doc = sys.modules[Cli.__module__].__doc__
        args = docopt(docstring=doc, argv=argv[1:], options_first=True)
        if args['COMMAND'] == 'scan':
            scanner.cli(argv[1:])
        else:
            print(f"Unrecognized command: {args['COMMAND']}")
            print()
            print(doc)
