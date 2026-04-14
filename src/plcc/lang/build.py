"""plcc-lang-build
    Dispatch to the appropriate plcc-<lang>-build command if it exists.

Usage:
    plcc-lang-build --target=LANG --output=DIR

Options:
    --target=LANG   Target language.
    --output=DIR    Output directory (already populated by plcc-lang-emit).
    -h --help       Show this message.
"""

import shutil
import subprocess
import sys

from docopt import docopt


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    lang = args['--target']
    output = args['--output']
    cmd = resolve_build_command(lang)
    if not shutil.which(cmd):
        sys.exit(0)  # No build step for this language — not an error
    result = subprocess.run([cmd, f'--output={output}'])
    sys.exit(result.returncode)


def resolve_build_command(lang):
    return f'plcc-{lang.lower()}-build'
