import enum
import sys

from plcc.cli import parse_args

from ...verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-diagram-plantuml-run
    Print the path to the rendered diagram image.

Usage:
    plcc-diagram-plantuml-run --input=FILE [-v ...] [options]

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
    args = parse_args(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-diagram-plantuml-run", Events, args)
    input_file = args['--input']
    verbose.emit(Events.STARTED, message=f"diagram ready: {input_file}")
    print(input_file)
    verbose.emit(Events.FINISHED)
