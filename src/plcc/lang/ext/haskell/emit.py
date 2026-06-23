"""plcc-haskell-emit
    Emit a Haskell interpreter from model JSON.

Usage:
    plcc-haskell-emit --output=DIR [-v ...] [options]

Options:
    --output=DIR    Directory to write output files into.
    -h --help       Show this message.
"""

import enum
import json
import shutil
import sys
from pathlib import Path

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = __doc__ + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-haskell-emit", Events, args)
    output_dir = Path(args['--output'])
    verbose.emit(Events.STARTED, message=f'emitting to {output_dir}')
    model = json.load(sys.stdin)
    emit(model, output_dir)
    verbose.emit(Events.FINISHED, message='done')


def emit(model, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    modules = _group_modules(model['classes'])
    _write_cabal(modules, output_dir)
    _copy_token(output_dir)


def _group_modules(classes):
    """Return dict mapping module_name -> module_info.

    module_info for an abstract rule:
        {'kind': 'abstract', 'abstract': cls_dict, 'concretes': [cls_dict, ...]}
    module_info for a lone concrete class (no abstract parent):
        {'kind': 'concrete', 'cls': cls_dict}
    """
    modules = {}
    for cls in classes:
        if cls['abstract']:
            modules[cls['name']] = {
                'kind': 'abstract',
                'abstract': cls,
                'concretes': [],
            }
    for cls in classes:
        if cls['abstract']:
            continue
        parent = cls['extends']
        if parent is not None and parent in modules:
            modules[parent]['concretes'].append(cls)
        else:
            modules[cls['name']] = {'kind': 'concrete', 'cls': cls}
    return modules


def _write_cabal(modules, output_dir):
    module_list = ', '.join(['Token'] + sorted(modules))
    content = (
        'cabal-version: 3.0\n'
        'name:          interpreter\n'
        'version:       0.1.0.0\n'
        '\n'
        'executable interpreter\n'
        '  main-is:          Main.hs\n'
        f'  other-modules:    {module_list}\n'
        '  build-depends:    base, aeson, bytestring, containers, text\n'
        '  default-language: Haskell2010\n'
        '  hs-source-dirs:   .\n'
    )
    (output_dir / 'interpreter.cabal').write_text(content)


def _copy_token(output_dir):
    src = Path(__file__).parent / 'runtime' / 'Token.hs'
    shutil.copy(src, output_dir / 'Token.hs')
