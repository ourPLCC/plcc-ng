"""plccng
    The Programming Languages Compiler Compiler - Next Generation

Usage:
    plccng COMMAND [OPTION ...] [ARGUMENT ...]
    plccng (-h|--help)

Commands:
    spec    Print JSON representation of PLCC spec.
    scan    Print JSON tokens given PLCC spec and code.

Options:
    -h|--help   Display this message
"""

import sys
from docopt import docopt

from . import scanner
from . import spec


def main():
    cli(sys.argv)


def cli(argv):
    Cli().run(argv)


class Cli:
    def run(self, argv):
        doc = sys.modules[Cli.__module__].__doc__
        args = docopt(docstring=doc, argv=argv[1:], options_first=True)
        if args['COMMAND'] in 'spec scan'.split():
            self._dispatchCommand(args['COMMAND'], argv[1:])
        else:
            print(f"Unrecognized command: {args['COMMAND']}")
            print()
            print(doc)

    def _dispatchCommand(self, command, argv):
        globals()[command].cli(argv)
