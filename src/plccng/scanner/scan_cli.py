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


def run(argv):
    argv = argv[1:]
    ScanCli().run(argv)


class ScanCli:
    def run(self, argv):
        doc = sys.modules[ScanCli.__module__].__doc__
        args = docopt(doc, argv)
        print(args)
