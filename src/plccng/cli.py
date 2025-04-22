"""
Usage:
  plccng scan --spec=SPEC [FILE ...]
  plccng spec [FILE]
  plccng (-h | --help)

Options:
  -h --help     Show this screen.

Commands:
  scan    Scan the given file.
"""

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
