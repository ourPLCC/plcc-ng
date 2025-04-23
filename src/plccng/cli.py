"""plccng

Usage:
  plccng scan --spec=SPEC [FILE ...]
  plccng spec [FILE]
  plccng (-h | --help)
"""

from plccng.scanner import cli as scanner_cli
import sys


def main():
    cli(sys.argv)


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

