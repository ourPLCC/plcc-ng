import base64
import enum
import sys
import urllib.request
import zlib

from plcc.cli import parse_args

from ...verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-diagram-plantuml-build
    Render a PlantUML diagram source file to a PNG image via plantuml.com.

Usage:
    plcc-diagram-plantuml-build --input=FILE --output=FILE [-v ...] [options]

Options:
    --input=FILE    Path to .puml source file.
    --output=FILE   Path to write .png image.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


_PLANTUML_ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
_BASE64_ALPHABET   = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
_B64_TO_PLANTUML = bytes.maketrans(
    _BASE64_ALPHABET.encode('utf-8'),
    _PLANTUML_ALPHABET.encode('utf-8'),
)


def _encode(source):
    compressed = zlib.compress(source.encode('utf-8'))
    return base64.b64encode(compressed[2:-4]).rstrip(b'=').translate(_B64_TO_PLANTUML).decode('utf-8')


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-diagram-plantuml-build", Events, args)
    input_file = args['--input']
    output_file = args['--output']
    verbose.emit(Events.STARTED, message=f"rendering {input_file}")
    try:
        with open(input_file) as f:
            source = f.read()
        url = f'https://www.plantuml.com/plantuml/png/{_encode(source)}'
        req = urllib.request.Request(url, headers={'User-Agent': 'plcc-ng/1.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            png_bytes = response.read()
    except Exception as e:
        print(f"plcc-diagram-plantuml-build: {e}", file=sys.stderr)
        sys.exit(1)
    with open(output_file, 'wb') as f:
        f.write(png_bytes)
    verbose.emit(Events.FINISHED, message=f"wrote {output_file}")
