import enum
import os
import subprocess
import sys

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-diagram
    Generate and display a class diagram from a PLCC grammar file.

Usage:
    plcc-diagram [-v ...] [options]

Options:
    --grammar-file=<path>   Path to the PLCC grammar file [default: grammar.plcc].
    --format=FMT            Diagram format [default: mermaid].
    -h --help               Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    try:
        args = docopt(__doc__, argv)
    except DocoptExit as e:
        print(str(e), file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-diagram --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose = VerboseContext.from_args("plcc-diagram", Events, args)
    grammar_file = args['--grammar-file']
    fmt = args['--format']

    if not os.path.exists(grammar_file):
        print(f"plcc-diagram: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-diagram --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message=f"generating diagram for {grammar_file}")
    child_flags = verbose.child_flags()

    make_result = subprocess.run(
        ['plcc-make', '--through=diagram',
         f'--grammar-file={grammar_file}',
         f'--diagram-format={fmt}'] + child_flags,
        stderr=subprocess.PIPE,
    )
    if make_result.returncode != 0:
        sys.exit(make_result.returncode)

    image_path = os.path.join('build', 'diagram', 'diagram.png')
    run_result = subprocess.run(
        ['plcc-diagram-run', f'--format={fmt}',
         f'--input={image_path}'] + child_flags,
        stderr=subprocess.PIPE,
    )
    if run_result.returncode != 0:
        sys.exit(run_result.returncode)

    verbose.emit(Events.FINISHED, message="done")
