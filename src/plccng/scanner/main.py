"""
Usage:
    scanner --spec=<specfile> [<file> ...]
    scanner (-h | --help)

Options:
    -h --help  Show this screen.
    --spec=<specfile>

Arguments:

    <specfile>      A path to a file containing a JSON formatted lexical spec.

    <file>          A path to an input file. If no files given, read from stdin.
                    If <file> is '-', read from stdin. When EOF is read, process
                    next file.

<specfile> Format:

    [
        {
            "Type": "Skip",
            "Name": "WHITESPACE",
            "Regex": "\\s+"  // Backslash is escape char in JSON. Then \\ is a single backslash; which is regex's escape char.
        },
        {
            "Type": "Token",
            "Name": "NUMBER",
            "Regex": "\\d+"
        }
    ]

Skip Format

    {
        "Type": "Skip",
        "Name": "WHITESPACE",
        "Lexeme": "         ",
        "File": "/workspace/cool/prog.cool",
        "Line": 3,
        "Column": 1
    }

Token Format:

    {
        "Type": "Token",
        "Name": "NUMBER",
        "Lexeme": "42",
        "File": "/workspace/cool/prog.cool",
        "Line": 3,
        "Column": 10
    }

LexError Format:

    {
        "Type": "LexError",
        "Unmatched": "+12=54"
        "File": "/workspace/cool/prog.cool",
        "Line": 3,
        "Column": 13
    }
"""

from docopt import docopt, DocoptExit
import sys
import json

class Main:
    def __init__(self, scanner, source):
        self.scanner = scanner
        self.source = source

    def run(self, stdin, stdout, stderr, argv):
        try:
            args = docopt(__doc__, argv)
        except DocoptExit:
            print("Missing --spec argument")
            sys.exit()

        if args["--spec"]:
            self._buildMatcherSpecFromSpecfile(args["--spec"])

            self._configureSourceFiles(args["<file>"])

        self.scanner.scan(list(self.source))

    def _buildMatcherSpecFromSpecfile(self, filePath):
        with open(filePath, "r") as file:
            data = json.load(file)
            self.scanner.matcher.spec = data

    def _configureSourceFiles(self, filePaths):
        if filePaths:
            self._appendSourceFiles(filePaths)
        else:
            self.source.files.append("-")

    def _appendSourceFiles(self, filePaths):
        for filePath in filePaths:
            self.source.files.append(filePath)
