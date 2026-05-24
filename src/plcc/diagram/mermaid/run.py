import enum
import os
import platform
import subprocess
import sys

from docopt import docopt

from ...verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-mermaid-diagram-run
    Open a diagram image in the system viewer.

Usage:
    plcc-mermaid-diagram-run --input=FILE [-v ...] [options]

Options:
    --input=FILE    Path to image file to open.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-mermaid-diagram-run", Events, args)
    input_file = args['--input']
    verbose.emit(Events.STARTED, message=f"opening {input_file}")
    _open_file(input_file)
    verbose.emit(Events.FINISHED)


def _open_file(path):
    system = platform.system()
    if system == 'Darwin':
        subprocess.run(['open', path], check=True)
    elif system == 'Windows':
        os.startfile(path)
    else:
        subprocess.run(['xdg-open', path], check=True)
