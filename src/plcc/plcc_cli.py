"""plcc
    The Programming Languages Compiler Compiler - Next Generation

Usage:
    plcc COMMAND [OPTION ...] [ARGUMENT ...]
    plcc (-h|--help)

Commands:
    spec    Print JSON representation of PLCC spec.

Options:
    -h|--help   Display this message
"""

import sys
from docopt import docopt

from . import spec


def main():
    run(sys.argv)


def run(argv):
    PlccCli().run(argv[1:])


class PlccCli:
    def run(self, argv):
        doc = sys.modules[PlccCli.__module__].__doc__
        args = docopt(docstring=doc, argv=argv, options_first=True)
        if args['COMMAND'] in 'spec'.split():
            self._dispatchCommand(args['COMMAND'], argv)
        else:
            print(f"Unrecognized command: {args['COMMAND']}")
            print()
            print(doc)

    def _dispatchCommand(self, command, argv):
        globals()[command].run(argv)
