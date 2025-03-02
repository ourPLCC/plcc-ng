"""
Usage:
    scanner --spec=<specfile> [<file> ...]
    scanner (-h | --help)
    scanner (-h | --help) [--spec=<specfile>] [<file> ...]
    scanner [--spec=<specfile>] [<file> ...]

Options:
    -h --help  Show this screen.
    --spec=<specfile>

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
            sys.exit()

        if args["--spec"]:
            self._buildMatcherSpecFromSpecfile(args["--spec"])

            if args["<file>"]:
                self._appendSourceFiles(args["<file>"])
            else:
                self.source.files.append("-")

        else:
            print("Missing --spec argument")
            sys.exit()

            # self._makeFileForStdinContents(stdin)


    def _buildMatcherSpecFromSpecfile(self, filePath):
        with open(filePath, "r") as file:
            data = json.load(file)
            self.scanner.matcher.spec = data

    def _appendSourceFiles(self, filePaths):
        for filePath in filePaths:
            self.source.files.append(filePath)

    # def _makeFileForStdinContents(self, stdin):
    #     contents = stdin.read()
    #     with open("-", "w") as file:
    #         file.write(contents)



