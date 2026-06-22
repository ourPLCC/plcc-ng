"""plcc-javascript-emit
    Emit a JavaScript interpreter from model JSON.

Usage:
    plcc-javascript-emit --output=DIR [-v ...] [options]

Options:
    --output=DIR    Directory to write output files into.
    -h --help       Show this message.
"""

import enum
import json
import shutil
import sys
from pathlib import Path

import jinja2
from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = __doc__ + VERBOSE_OPTIONS

_DEFAULT_ENTRY_POINT = '_run'

_START_JS = """\
const { Node } = require('./runtime/base');

class _Start extends Node {
    _run() {
        console.log(String(this));
    }
}

module.exports = { _Start };
"""


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-javascript-emit", Events, args)
    output_dir = Path(args['--output'])
    verbose.emit(Events.STARTED, message=f'emitting to {output_dir}')

    model = json.load(sys.stdin)
    output_dir.mkdir(parents=True, exist_ok=True)

    _copy_runtime(output_dir)

    classes = model['classes']
    start_class_name = model['start'][0].upper() + model['start'][1:]
    section = _find_javascript_section(model)
    entry_point = _DEFAULT_ENTRY_POINT
    fragments_by_class = _group_fragments(section.get('fragments', []) if section else [])

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(Path(__file__).parent / 'templates')),
        keep_trailing_newline=True,
    )
    class_template = env.get_template('class_file.js.jinja')
    main_template = env.get_template('main.js.jinja')

    for cls in classes:
        cls = dict(cls)
        if cls['name'] == start_class_name and cls['extends'] is None:
            cls['extends'] = '_Start'
        frags = fragments_by_class.get(cls['name'], [])
        content = class_template.render(
            cls=cls,
            top_fragments=[f for f in frags if f['kind'] == 'top'],
            import_fragments=[f for f in frags if f['kind'] == 'import'],
            init_fragments=[f for f in frags if f['kind'] == 'init'],
            body_fragments=[f for f in frags if f['kind'] == 'body'],
        )
        (output_dir / f"{cls['name']}.js").write_text(content)

    (output_dir / '_Start.js').write_text(_START_JS)

    all_frags = section.get('fragments', []) if section else []
    for frag in all_frags:
        if frag['kind'] == 'file':
            (output_dir / f"{frag['class_name']}.js").write_text(frag['body'])

    main_content = main_template.render(classes=classes, entry_point=entry_point)
    (output_dir / 'main.js').write_text(main_content)

    verbose.emit(Events.FINISHED, message='done')


def _copy_runtime(output_dir):
    src = Path(__file__).parent / 'runtime'
    dst = output_dir / 'runtime'
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('*_test.py'))


def _find_javascript_section(model):
    for s in model.get('semantic_sections', []):
        if s.get('language', '').lower() == 'javascript':
            return s
    return None


def _group_fragments(fragments):
    groups = {}
    for frag in fragments:
        groups.setdefault(frag['class_name'], []).append(frag)
    return groups
