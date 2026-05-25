import enum
import sys

from docopt import docopt

from ...verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-plantuml-diagram-run
    Print the path to the rendered diagram image.

Usage:
    plcc-plantuml-diagram-run --input=FILE [-v ...] [options]

Options:
    --input=FILE    Path to image file.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-plantuml-diagram-run", Events, args)
    input_file = args['--input']
    verbose.emit(Events.STARTED, message=f"diagram ready: {input_file}")
    print(input_file)
    verbose.emit(Events.FINISHED)
