"""plcc-java-build
    Compile generated Java source files.

Usage:
    plcc-java-build --output=DIR [options]

Options:
    --output=DIR    Directory containing generated Java files.
    -h --help       Show this message.
"""

import enum
import glob
import os
import subprocess
import sys

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
    verbose = VerboseContext.from_args("plcc-java-build", Events, args)
    output_dir = args['--output']
    verbose.emit(Events.STARTED, message=f'compiling in {output_dir}')
    java_files = glob.glob(os.path.join(output_dir, '*.java'))
    if not java_files:
        verbose.emit(Events.FINISHED, message='no .java files found')
        return
    result = subprocess.run(['javac'] + java_files, cwd=output_dir)
    if result.returncode != 0:
        print('plcc-java-build: javac failed', file=sys.stderr)
        sys.exit(result.returncode)
    verbose.emit(Events.FINISHED, message='done')
