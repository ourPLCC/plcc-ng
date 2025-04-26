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

from . import scan
from . import spec


def main():
    run(sys.argv)


def run(argv):
    PlccngCli().run(argv[1:])


class PlccngCli:
    def run(self, argv):
        doc = sys.modules[PlccngCli.__module__].__doc__
        args = docopt(docstring=doc, argv=argv, options_first=True)
        if args['COMMAND'] in 'spec scan'.split():
            self._dispatchCommand(args['COMMAND'], argv)
        else:
            print(f"Unrecognized command: {args['COMMAND']}")
            print()
            print(doc)

    def _dispatchCommand(self, command, argv):
        globals()[command].run(argv)
