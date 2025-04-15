"""
Usage:
  plccng scan [OPTIONS ...]
  plccng (-h | --help)

Options:
  -h --help     Show this screen.

Commands:
  scan    Scan input and print tokens as JSON objects.
"""

import sys

from docopt import docopt

from . import scanner


def plccng(argv):
    Plccng().run(argv)


class Plccng:
    def __init__(self):
        ...

    def run(self, argv):
      cli = sys.modules[Plccng.__module__]
      args = docopt(cli.__doc__, argv)
      if args["scan"]:
          scanner.run(argv)
      else:
          print("Invalid Command, Enter 'plccng -h' for help")


def main():
  plccng(sys.argv)
