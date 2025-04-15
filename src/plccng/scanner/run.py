'''plccng scan

    Scans one or more input files and
    prints tokens and lexing errors as JSON objects to stdout.

Usage:

    plccng scan --spec=<specfile> [<file> ...]

Arguments:

    <specfile>      A path to a file containing a JSON formatted lexical spec.

    <file>          A path to an input file. If no files given, read from stdin.
                    If <file> is '-', read from stdin. When EOF is read, process
                    next file.

Output Format:

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
            "File": "/workspace/cool/prog.cool",
            "Line": 3,
            "Column": 13
        }
'''

from docopt import docopt

def run(args):
    print(args)
    # docopt(__doc__, args)
