import enum
import json
import os
import sys

from docopt import docopt

from ....verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-plantuml-emit
    Emit PlantUML class diagram from model JSON.

Usage:
    plcc-plantuml-emit --output=DIR [options]

Options:
    --output=DIR    Directory to write output files into.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-plantuml-emit", Events, args)
    output_dir = args['--output']
    os.makedirs(output_dir, exist_ok=True)
    model = json.load(sys.stdin)
    for cls in model.get('classes', []):
        _emit_class(cls, output_dir)


def _emit_class(cls, output_dir):
    # Design choice: one .puml file per class (not one combined diagram).
    # Each file is a self-contained class box. Phase 1 produces one file for the
    # trivial grammar; grammars with multiple classes produce N separate files.
    # A combined hierarchy diagram is deferred until there is a grammar that
    # exercises it (Phase 2+).
    name = cls['name']
    fields = cls.get('fields', [])
    lines = ['@startuml', f'class {name} {{']
    for field in fields:
        lines.append(f'  {field["name"]}: {field["type"]}')
    lines += ['}', '@enduml']
    path = os.path.join(output_dir, f'{name.lower()}.puml')
    with open(path, 'w') as f:
        f.write('\n'.join(lines) + '\n')
