import enum
import json
import os
import sys

from docopt import docopt

from ...verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-plantuml-diagram-emit
    Emit a PlantUML class diagram from model JSON.

Usage:
    plcc-plantuml-diagram-emit [--output=DIR] [-v ...] [options]

Options:
    --output=DIR    Directory to write diagram.puml into (writes to stdout if omitted).
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-plantuml-diagram-emit", Events, args)
    output_dir = args['--output']
    model = json.load(sys.stdin)
    content = build_diagram(model)
    if output_dir is None:
        sys.stdout.write(content)
    else:
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, 'diagram.puml')
        with open(path, 'w') as f:
            f.write(content)


def build_diagram(model):
    lines = ['@startuml']
    classes = model.get('classes', [])
    for i, cls in enumerate(classes):
        if i > 0:
            lines.append('')
        lines.extend(_render_class(cls))
        if cls.get('extends'):
            lines.append(f'{cls["name"]} --|> {cls["extends"]}')
    lines.append('@enduml')
    return '\n'.join(lines) + '\n'


def _render_class(cls):
    if cls.get('abstract'):
        return [f'abstract class {cls["name"]}']
    result = [f'class {cls["name"]} {{']
    for field in cls.get('fields', []):
        result.append(f'  {field["name"]}: {field["type"]}')
    result.append('}')
    return result
