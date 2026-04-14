"""plcc-model
    Transform spec JSON into a language-neutral code model.

Usage:
    plcc-model [options] [SPEC_JSON]

Arguments:
    SPEC_JSON   Path to spec JSON file. Use - or omit to read from stdin.

Options:
    -h --help   Show this message.
"""

import json
import sys

from docopt import docopt

from .build_model import build_model


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    path = args['SPEC_JSON'] or '-'
    spec = _load(path)
    model = build_model(spec)
    print(json.dumps(model, indent=2))


def _load(path):
    if path == '-':
        return json.load(sys.stdin)
    with open(path) as f:
        return json.load(f)
