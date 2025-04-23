"""plccng scan
    Print token in JSON given PLCC specification and input files.

Usage:
    plccng scan --spec=SPEC [FILE ...]
    plccng scan (-h|--help)

Arguments:
    --spec=SPEC     Path to a PLCC specification file.
    FILE            A sequence of input files. If none are given, stdin is used.
                    If '-' is given for a file, stdin is used.
"""

import sys

from docopt import docopt


def cli(argv):
    Cli().run(argv)

class Cli:
    def run(self, argv):
        doc = sys.modules[Cli.__module__].__doc__
        args = docopt(doc, argv)
        print(args)
