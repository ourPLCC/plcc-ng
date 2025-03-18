from docopt import docopt
import sys
# from spec import scan, parse, etc. Will need to figure out names and location
"""
Usage:
  plccng scan <file>
  plccng parse <file>
  plccng run <file>
  plccng rep <file>
  plccng (-h | --help)
  plccng --version

Options:
  -h --help     Show this screen.

Commands:
  scan    Scan the given file.
  parse   Parse the given file.
  run     Execute the given file.
  rep     Generate a report for the given file.
"""


def main():
    args = docopt(__doc__)

    if args["scan"]:
        scan.run(args["<file>"])
    elif args["parse"]:
        parse.run(args["<file>"])
    elif args["run"]:
        run.run(args["<file>"])
    elif args["rep"]:
        rep.run(args["<file>"])
    else:
        print("Invalid Command, Enter 'plccng -h' for help")
