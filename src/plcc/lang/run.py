"""plcc-lang-run
    Dispatch to the appropriate plcc-<lang>-run command.

Usage:
    plcc-lang-run --target=LANG --output=DIR [-v ...] [options]

Options:
    --target=LANG   Target language (e.g. Python, Java).
    --output=DIR    Directory containing built artifacts.
    -h --help       Show this message.
"""

import enum
import shutil
import subprocess
import sys

from plcc.cli import parse_args

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = __doc__ + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-lang-run", Events, args)
    lang = args["--target"]
    output = args["--output"]
    cmd = f"plcc-{lang.lower()}-run"
    if not shutil.which(cmd):
        # No-op pattern: exit 0 silently if no runner for this language
        sys.exit(0)
    verbose.emit(Events.STARTED, message=f"dispatching to {cmd}")
    child_cmd = [cmd, f"--output={output}"] + verbose.child_flags()
    try:
        result = subprocess.run(child_cmd, stdin=sys.stdin)
    except KeyboardInterrupt:
        sys.exit(130)
    verbose.emit(Events.FINISHED, message=f"exit {result.returncode}")
    sys.exit(result.returncode)
