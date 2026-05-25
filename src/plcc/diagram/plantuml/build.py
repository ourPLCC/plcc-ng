import enum
import sys

from docopt import docopt

from ...verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-plantuml-diagram-build
    Render a PlantUML diagram source file to a PNG image via plantuml.com.

Usage:
    plcc-plantuml-diagram-build --input=FILE --output=FILE [-v ...] [options]

Options:
    --input=FILE    Path to .puml source file.
    --output=FILE   Path to write .png image.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-plantuml-diagram-build", Events, args)
    input_file = args['--input']
    output_file = args['--output']
    verbose.emit(Events.STARTED, message=f"rendering {input_file}")
    try:
        import plantuml as plantuml_lib
    except ImportError:
        print(
            "plcc-plantuml-diagram-build: plantuml not installed — "
            "run: pip install plcc-ng[diagram]",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        server = plantuml_lib.PlantUML(
            url='https://www.plantuml.com/plantuml/png/',
            request_opts={'timeout': 30},
        )
        with open(input_file) as f:
            source = f.read()
        png_bytes = server.processes(source)
    except Exception as e:
        print(f"plcc-plantuml-diagram-build: {e}", file=sys.stderr)
        sys.exit(1)
    with open(output_file, 'wb') as f:
        f.write(png_bytes)
    verbose.emit(Events.FINISHED, message=f"wrote {output_file}")
