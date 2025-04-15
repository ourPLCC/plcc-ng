"""plccng

Usage:
  plccng scan [OPTIONS ...]
  plccng (-h | --help)

Arguments:
  -h | --help      Show this screen.

Commands:
  scan    Scan input and print tokens as JSON objects.
"""

import sys

from docopt import docopt

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


def main():
    cli(sys.argv[1:])
