"""
Usage: scanner [--help|-h]
"""

from docopt import docopt


class Main:
    def __init__(self, scanner, source):
        self.scanner = scanner
        self.source = source

    def run(stdin, stdout, stderr, argv):
        arguments = docopt(__doc__, argv)
        return arguments



