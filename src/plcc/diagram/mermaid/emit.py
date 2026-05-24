import enum
import json
import sys

from docopt import docopt

from ...verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-mermaid-diagram-emit
    Emit a Mermaid class diagram from model JSON.

Usage:
    plcc-mermaid-diagram-emit [-v ...] [options]

Options:
    -h --help   Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-mermaid-diagram-emit", Events, args)
    verbose.emit(Events.STARTED)
    model = json.load(sys.stdin)
    sys.stdout.write(build_diagram(model))
    verbose.emit(Events.FINISHED)


def build_diagram(model):
    lines = ['classDiagram']
    classes = model.get('classes', [])
    for cls in classes:
        lines.extend(_render_class(cls))
    for cls in classes:
        if cls.get('extends'):
            lines.append(f'    {cls["name"]} --|> {cls["extends"]}')
    return '\n'.join(lines) + '\n'


def _render_class(cls):
    name = cls['name']
    result = [f'    class {name} {{']
    if cls.get('abstract'):
        result.append('        <<abstract>>')
    for field in cls.get('fields', []):
        result.append(f'        {field["name"]}: {field["type"]}')
    result.append('    }')
    return result
