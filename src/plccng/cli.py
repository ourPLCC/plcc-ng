from docopt import docopt
from . import scanner

import sys

"""
Usage:
  plccng scan --spec=<specfile> [<file> ...]
  plccng (-h | --help)

Options:
  -h --help     Show this screen.

Commands:
  scan    Scan the given file.
"""


def main():
    args = docopt(__doc__)

    if args["scan"]:
        scanner.run(args)
    else:
        print("Invalid Command, Enter 'plccng -h' for help")
