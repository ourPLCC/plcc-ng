import base64
import enum
import sys
import urllib.error
import urllib.request
import zlib

from docopt import docopt

from ...verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-mermaid-diagram-build
    Render a Mermaid diagram source file to a PNG image via kroki.io.

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


def _encode(source):
    compressed = zlib.compress(source.encode('utf-8'), 9)
    return base64.urlsafe_b64encode(compressed).decode('utf-8').rstrip('=')


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-mermaid-diagram-build", Events, args)
    input_file = args['--input']
    output_file = args['--output']
    verbose.emit(Events.STARTED, message=f"rendering {input_file}")
    try:
        with open(input_file) as f:
            source = f.read()
        url = f'https://kroki.io/mermaid/png/{_encode(source)}'
        req = urllib.request.Request(url, headers={'User-Agent': 'plcc-ng/1.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            png_bytes = response.read()
    except Exception as e:
        print(f"plcc-mermaid-diagram-build: {e}", file=sys.stderr)
        sys.exit(1)
    with open(output_file, 'wb') as f:
        f.write(png_bytes)
    verbose.emit(Events.FINISHED, message=f"wrote {output_file}")
