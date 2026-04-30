"""plcc-java-build
    Compile generated Java source files.

Usage:
    plcc-java-build --output=DIR [options]

Options:
    --output=DIR    Directory containing generated Java files.
    -h --help       Show this message.
"""

import enum
import subprocess
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
    verbose = VerboseContext.from_args("plcc-java-build", Events, args)
    output_dir = Path(args['--output']).resolve()
    verbose.emit(Events.STARTED, message=f'compiling in {output_dir}')
    java_files = list(output_dir.glob('*.java'))
    runtime_java_files = list((output_dir / 'runtime').glob('*.java'))
    if not java_files and not runtime_java_files:
        verbose.emit(Events.FINISHED, message='no .java files found')
        return
    json_jars = list((output_dir / 'runtime').glob('org.json*.jar'))
    if not json_jars:
        print('plcc-java-build: org.json jar not found in runtime/', file=sys.stderr)
        sys.exit(1)
    json_jar = str(json_jars[0])
    result = subprocess.run(
        ['javac', '-cp', json_jar] + [str(f) for f in java_files + runtime_java_files],
        cwd=str(output_dir),
    )
    if result.returncode != 0:
        print('plcc-java-build: javac failed', file=sys.stderr)
        sys.exit(result.returncode)
    verbose.emit(Events.FINISHED, message='done')
