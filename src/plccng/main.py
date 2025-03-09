"""
Usage:
    plccng scan --spec=<specfile> [<file> ...]
    plccng (-h | --help)

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

class Main:
    def __init__(self, scannerMain):
        self.scannerMain = scannerMain

    def run(self, stdin, stdout, stderr, argv):
        try:
            args = docopt(__doc__, argv)
        except DocoptExit:
            print("Invalid arguments, Enter 'plccng -h' for help.")
            sys.exit()

        if args['scan']:
            self.scannerMain.args = self._buildRequiredArgumentsForScannerMain(args)
            self.scannerMain.run()

    def _buildRequiredArgumentsForScannerMain(self, args):
        newDict = {}
        newDict['--spec'] = args['--spec']
        newDict['<file>'] = args['<file>'] if len(args['<file>']) > 0 else ['-']
        return newDict





