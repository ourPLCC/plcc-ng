"""
Usage:
    scanner (-h | --help)

Options:
    -h --help  Show this screen.
"""

from docopt import docopt
from .main_help_message import helpMessage
import sys

class Main:
    def __init__(self, scanner, source):
        self.scanner = scanner
        self.source = source

    def run(self, stdin, stdout, stderr, argv):
        args = docopt(__doc__, argv, default_help=False)
        if args["--help"]:
            print(helpMessage)


# if __name__ == "__main__":
#     scanner = Main(None, None)
#     scanner.run(None, None, None, argv=sys.argv[1:])
#     # print(sys.argv[1:])

