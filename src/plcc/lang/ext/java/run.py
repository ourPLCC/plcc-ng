"""plcc-java-run
    Run a compiled Java interpreter.

Usage:
    plcc-java-run --output=DIR [options]

Options:
    --output=DIR    Directory containing compiled Java class files.
    -h --help       Show this message.
"""

import enum
import os
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
    verbose = VerboseContext.from_args("plcc-java-run", Events, args)
    output_dir = Path(args['--output']).resolve()
    verbose.emit(Events.STARTED, message=f'running Main in {output_dir}')
    json_jars = list((output_dir / 'runtime').glob('org.json*.jar'))
    if not json_jars:
        print('plcc-java-run: org.json jar not found in runtime/', file=sys.stderr)
        sys.exit(1)
    json_jar = str(json_jars[0])
    classpath = f"{output_dir}{os.pathsep}{json_jar}"
    result = subprocess.run(
        ['java', '-cp', classpath, 'Main'],
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    verbose.emit(Events.FINISHED, message=f'exit {result.returncode}')
    sys.exit(result.returncode)
