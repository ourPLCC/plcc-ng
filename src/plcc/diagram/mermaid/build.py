import enum
import shutil
import subprocess
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
    if not shutil.which('mmdc'):
        print(
            "plcc-mermaid-diagram-build: mmdc not found — "
            "run: npm install -g @mermaid-js/mermaid-cli",
            file=sys.stderr,
        )
        sys.exit(1)
    result = subprocess.run(
        ['mmdc', '-i', input_file, '-o', output_file],
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode('utf-8', errors='replace').strip()
        print(f"plcc-mermaid-diagram-build: mmdc failed: {stderr}", file=sys.stderr)
        sys.exit(result.returncode)
    verbose.emit(Events.FINISHED, message=f"wrote {output_file}")
