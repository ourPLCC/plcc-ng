"""
Usage:
    scanner --specfile=<specfile> [<file> ...]
    scanner (-h | --help)

Options:
    -h --help  Show this screen.
    --specfile=<specfile>

"""

from docopt import docopt
from .main_help_message import helpMessage
import sys
import json

class Main:
    def __init__(self, scanner, source):
        self.scanner = scanner
        self.source = source

    def run(self, stdin, stdout, stderr, argv):
        args = docopt(__doc__, argv, default_help=False)
        if args["--help"]:
            print(helpMessage)

        if args["--specfile"]:
            self._buildMatcherSpecFromSpecfile(args)

        if args["<file>"]:
            for file in args["<file>"]:
                self.source.files.append(file)

        if stdin:
            # self._makeFileForStdinContents(stdin)
            self._addStdinInputFileNameToSourceFiles()

    def _buildMatcherSpecFromSpecfile(self, args):
        with open(args["--specfile"], "r") as file:
                data = json.load(file)
                self.scanner.matcher.spec = data

    # def _makeFileForStdinContents(self, stdin):
    #     contents = stdin.read()
    #     with open("-", "w") as file:
    #         file.write(contents)

    def _addStdinInputFileNameToSourceFiles(self):
        self.source.files.append("-")


