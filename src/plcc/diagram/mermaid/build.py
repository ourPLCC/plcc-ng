import enum
import sys

from docopt import docopt

from ...verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-mermaid-diagram-build
    Render a Mermaid diagram source file to a PNG image.

Usage:
    plcc-mermaid-diagram-build --input=FILE --output=FILE [-v ...] [options]

Options:
    --input=FILE    Path to .mmd source file.
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
    verbose = VerboseContext.from_args("plcc-mermaid-diagram-build", Events, args)
    input_file = args['--input']
    output_file = args['--output']
    verbose.emit(Events.STARTED, message=f"rendering {input_file}")
    try:
        from mmdc import MermaidConverter
    except ImportError:
        print(
            "plcc-mermaid-diagram-build: mmdc not installed — "
            "run: pip install plcc[diagram]",
            file=sys.stderr,
        )
        sys.exit(1)
    source = open(input_file).read()
    converter = MermaidConverter()
    png_bytes = converter.to_png(source)
    with open(output_file, 'wb') as f:
        f.write(png_bytes)
    verbose.emit(Events.FINISHED, message=f"wrote {output_file}")
