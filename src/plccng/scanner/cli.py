"""plccng scan

Usage:
  plccng scan

Arguments:
  -h      Show this screen.
"""

import sys

from docopt import docopt


def cli(argv):
    Cli().run(argv)

class Cli:
    def run(self, argv):
        doc = sys.modules[Cli.__module__].__doc__
        args = docopt(doc, argv)
